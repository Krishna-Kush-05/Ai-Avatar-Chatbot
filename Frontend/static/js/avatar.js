import * as THREE from 'https://unpkg.com/three@0.160.0/build/three.module.js';
import { FBXLoader } from 'https://unpkg.com/three@0.160.0/examples/jsm/loaders/FBXLoader.js';

let scene, camera, renderer;
let avatar, mixer;
let avatarHeadMesh = null;

// Shape Key Indices
let mouthKeyIndex = null;
let mouthWideKeyIndex = null; // e.g. E, I, Smile, Stretch
let mouthOKeyIndex = null;    // e.g. O, U, Pucker, Funnel
let blinkKeyIndex = null;

// State Flags
// window.isTalking is the SHARED flag set by script.js via audio onplay/onended.
// avatar.js reads it here so lip-sync stays in sync with actual audio playback.
// The local `isTalking` below is only used as a fallback when avatarSpeak() is
// called directly (Web Audio API path).
let isTalking = false;

// Speech Logic Variables
let speechTarget = 0;
let wideTarget = 0;
let oTarget = 0;
let lastSpeechUpdate = 0;
let speechSpeed = 150;

// Audio analyser for real lip-sync
let audioAnalyser = null;
let audioDataArray = null;

// Blink Logic Variables
let isBlinking = false;
let blinkTarget = 0;
let lastBlinkTime = 0;
let nextBlinkInterval = 3000;

window.addEventListener('DOMContentLoaded', () => {
    initAvatar();
});

/**
 * Connects the avatar's lip-sync to an Audio element.
 * Called from script.js when TTS audio starts playing.
 */
window.avatarSpeak = function (audioElement) {
    if (!audioElement) return;

    try {
        // Create audio context and analyser for real lip-sync
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const source = audioCtx.createMediaElementSource(audioElement);
        audioAnalyser = audioCtx.createAnalyser();
        audioAnalyser.fftSize = 256;
        audioDataArray = new Uint8Array(audioAnalyser.frequencyBinCount);

        source.connect(audioAnalyser);
        audioAnalyser.connect(audioCtx.destination);

        isTalking = true;

        audioElement.addEventListener('ended', () => {
            isTalking = false;
            audioAnalyser = null;
            audioDataArray = null;
        });

        audioElement.addEventListener('pause', () => {
            isTalking = false;
        });

        audioElement.addEventListener('play', () => {
            isTalking = true;
        });
    } catch (e) {
        // Fallback: use simple procedural talking if Web Audio API fails
        isTalking = true;
        audioElement.addEventListener('ended', () => { isTalking = false; });
        audioElement.addEventListener('pause', () => { isTalking = false; });
        audioElement.addEventListener('play', () => { isTalking = true; });
    }
};

function initAvatar() {
    const container = document.getElementById('avatar-canvas');
    if (!container) return;

    // 1. SCENE
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x111827);

    // 2. CAMERA - Frame face + chest (avatar spans y=-0.8 to y≈0.8)
    camera = new THREE.PerspectiveCamera(32, container.clientWidth / container.clientHeight, 0.1, 1000);
    camera.position.set(0, 0.6, 0.8);

    // 3. RENDERER
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    container.appendChild(renderer.domElement);

    // 4. LIGHTS
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.2);
    scene.add(ambientLight);
    const mainLight = new THREE.DirectionalLight(0xffffff, 2.0);
    mainLight.position.set(2, 2, 5);
    scene.add(mainLight);

    // 5. LOAD AVATAR
    const loader = new FBXLoader();
    loader.load('/static/models/Catwalk Idle.fbx', (object) => {
        avatar = object;
        scene.add(avatar);

        // Scale & Position
        const box = new THREE.Box3().setFromObject(avatar);
        const size = box.getSize(new THREE.Vector3());
        if (size.y > 0) {
            const scaleFactor = 1.6 / size.y;
            avatar.scale.multiplyScalar(scaleFactor);
        }

        const newBox = new THREE.Box3().setFromObject(avatar);
        const center = newBox.getCenter(new THREE.Vector3());
        avatar.position.x = -center.x;
        avatar.position.z = -center.z;
        avatar.position.y = -0.8;

        // Frame face+chest: look at mid-chest/neck area
        camera.lookAt(0, 0.65, 0);

        // Texture Fix
        avatar.traverse((child) => {
            if (child.isMesh) {
                const oldMap = child.material ? child.material.map : null;
                const color = oldMap ? 0xffffff : 0xcccccc;
                child.material = new THREE.MeshStandardMaterial({
                    color: color,
                    map: oldMap,
                    roughness: 0.5,
                    metalness: 0.1,
                    side: THREE.DoubleSide
                });
            }
        });

        setupMusclesAndAnimation(object);
        animate();

    }, undefined, (e) => console.error('Avatar load error:', e));

    // Handle resize
    const resizeObserver = new ResizeObserver(() => {
        if (!container || !renderer || !camera) return;
        const w = container.clientWidth;
        const h = container.clientHeight;
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
        renderer.setSize(w, h);
    });
    resizeObserver.observe(container);
}

function setupMusclesAndAnimation(object) {
    // 1. Find the Head
    avatarHeadMesh = avatar.getObjectByName('AvatarHead');
    if (!avatarHeadMesh) {
        avatar.traverse((child) => {
            if (child.isMesh && child.morphTargetDictionary && !avatarHeadMesh) {
                if (!child.name.includes("Eyelash") && !child.name.includes("Teeth")) avatarHeadMesh = child;
            }
        });
    }

    if (avatarHeadMesh && avatarHeadMesh.morphTargetDictionary) {
        const keys = Object.keys(avatarHeadMesh.morphTargetDictionary);

        // 2. Find Mouth (Talking)
        const mouthKeyName = keys.find(k => k.toLowerCase() === 'jawopen') ||
            keys.find(k => k.toLowerCase() === 'mouthopen') ||
            keys.find(k => k.toLowerCase() === 'viseme_aa');
        if (mouthKeyName) {
            mouthKeyIndex = avatarHeadMesh.morphTargetDictionary[mouthKeyName];
        }

        // 2a. Find Wide Mouth (E, I, Smile, Stretch)
        const wideKeyName = keys.find(k => k.toLowerCase().includes('smile') ||
            k.toLowerCase() === 'mouthstretch' ||
            k.toLowerCase() === 'viseme_e' ||
            k.toLowerCase() === 'viseme_i');
        if (wideKeyName) mouthWideKeyIndex = avatarHeadMesh.morphTargetDictionary[wideKeyName];

        // 2b. Find Round Mouth (O, U, Pucker, Funnel)
        const oKeyName = keys.find(k => k.toLowerCase().includes('pucker') ||
            k.toLowerCase().includes('funnel') ||
            k.toLowerCase() === 'viseme_o' ||
            k.toLowerCase() === 'viseme_u');
        if (oKeyName) mouthOKeyIndex = avatarHeadMesh.morphTargetDictionary[oKeyName];

        // 3. Find Eyes (Blinking)
        const blinkKeyName = keys.find(k => k.toLowerCase().includes('blink') ||
            k.toLowerCase().includes('eyeclose'));
        if (blinkKeyName) {
            blinkKeyIndex = avatarHeadMesh.morphTargetDictionary[blinkKeyName];
        }
    }

    // 4. Body Animation
    if (object.animations && object.animations.length > 0) {
        mixer = new THREE.AnimationMixer(avatar);
        const action = mixer.clipAction(object.animations[0]);
        action.play();
    }
}

function animate() {
    requestAnimationFrame(animate);
    const now = Date.now();

    // Update Body Animation
    if (mixer) mixer.update(0.016);

    if (avatarHeadMesh) {
        // --- TALKING (Audio-driven or procedural fallback) ---
        if (mouthKeyIndex !== null || mouthWideKeyIndex !== null || mouthOKeyIndex !== null) {
            // Prefer window.isTalking (set by script.js audio events) so lip-sync
            // matches actual audio playback.  Fall back to local isTalking when
            // avatarSpeak() drives the Web Audio analyser path.
            const talking = (typeof window.isTalking !== 'undefined') ? window.isTalking : isTalking;
            if (talking) {
                // Procedural varied lip sync (creates more natural varied mouth shapes)
                if (now - lastSpeechUpdate > speechSpeed) {
                    // Pick a random viseme shape
                    const rand = Math.random();
                    if (rand < 0.25) {
                        // Pause / closed
                        speechTarget = 0; wideTarget = 0; oTarget = 0;
                    } else if (rand < 0.5) {
                        // Jaw open heavily (A, ah)
                        speechTarget = 0.4 + (Math.random() * 0.4);
                        wideTarget = 0; oTarget = 0;
                    } else if (rand < 0.75) {
                        // Wide mouth (E, eee, smile)
                        speechTarget = 0.1 + (Math.random() * 0.2);
                        wideTarget = 0.3 + (Math.random() * 0.3);
                        oTarget = 0;
                    } else {
                        // Round mouth (O, u, pucker)
                        speechTarget = 0.1 + (Math.random() * 0.2);
                        wideTarget = 0;
                        oTarget = 0.4 + (Math.random() * 0.4);
                    }

                    lastSpeechUpdate = now;
                    // Vary the speed of the shape changes (syllable speed)
                    speechSpeed = 80 + Math.random() * 120;
                }
            } else {
                // Not talking, close all
                speechTarget = 0;
                wideTarget = 0;
                oTarget = 0;
            }

            // Smoothly move jaws to targets
            if (mouthKeyIndex !== null) {
                const currentMouth = avatarHeadMesh.morphTargetInfluences[mouthKeyIndex];
                const lerpRateJaw = (speechTarget < currentMouth) ? 0.35 : 0.25;
                avatarHeadMesh.morphTargetInfluences[mouthKeyIndex] = THREE.MathUtils.lerp(currentMouth, speechTarget, lerpRateJaw);
            }

            if (mouthWideKeyIndex !== null) {
                const currentWide = avatarHeadMesh.morphTargetInfluences[mouthWideKeyIndex];
                const lerpRateWide = (wideTarget < currentWide) ? 0.4 : 0.2;
                avatarHeadMesh.morphTargetInfluences[mouthWideKeyIndex] = THREE.MathUtils.lerp(currentWide, wideTarget, lerpRateWide);
            }

            if (mouthOKeyIndex !== null) {
                const currentO = avatarHeadMesh.morphTargetInfluences[mouthOKeyIndex];
                const lerpRateO = (oTarget < currentO) ? 0.4 : 0.2;
                avatarHeadMesh.morphTargetInfluences[mouthOKeyIndex] = THREE.MathUtils.lerp(currentO, oTarget, lerpRateO);
            }
        }

        // --- BLINKING ---
        if (blinkKeyIndex !== null) {
            if (!isBlinking && now - lastBlinkTime > nextBlinkInterval) {
                isBlinking = true;
                blinkTarget = 1;
            }

            if (isBlinking) {
                const currentBlink = avatarHeadMesh.morphTargetInfluences[blinkKeyIndex];
                avatarHeadMesh.morphTargetInfluences[blinkKeyIndex] = THREE.MathUtils.lerp(currentBlink, blinkTarget, 0.3);

                if (blinkTarget === 1 && currentBlink > 0.9) {
                    blinkTarget = 0;
                }
                if (blinkTarget === 0 && currentBlink < 0.1) {
                    isBlinking = false;
                    lastBlinkTime = now;
                    nextBlinkInterval = 2000 + Math.random() * 4000;
                }
            }
        }
    }

    renderer.render(scene, camera);
}