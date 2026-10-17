/**
 * Sound regression checks (npm run check:sound).
 *
 * 1. Generated assets: every cue has a file, effects are short and finite,
 *    the two ambience loops are long enough and join without a seam.
 * 2. lib/sound.ts runs with React, storage, the platform and expo-audio
 *    replaced at their boundaries. This proves preferences, the web gesture
 *    gate, de-duplication and ambience start/stop decisions. It does not prove
 *    real audio output, browser autoplay policy, iOS silent mode or mixing.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');

const root = path.join(__dirname, '..');
let checks = 0;
const check = (condition, message) => {
  assert.ok(condition, message);
  checks++;
};
const compile = (file) =>
  ts.transpileModule(fs.readFileSync(path.join(root, file), 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText;

// ------------------------------------------------------------------ assets
const assetsModule = { exports: {} };
vm.runInNewContext(compile('lib/sound-assets.ts'), {
  module: assetsModule,
  exports: assetsModule.exports,
  require: (id) => {
    assert.ok(id.startsWith('@/assets/sounds/'), `Unexpected sound asset import: ${id}`);
    return { __esModule: true, default: id.replace('@/', '') };
  },
});
const { soundEffects, ambienceLoops, soundDurations } = assetsModule.exports;

function readWav(file) {
  const buffer = fs.readFileSync(path.join(root, file));
  check(buffer.toString('ascii', 0, 4) === 'RIFF', `${file} is a RIFF file`);
  const channels = buffer.readUInt16LE(22);
  const rate = buffer.readUInt32LE(24);
  const bits = buffer.readUInt16LE(34);
  const dataAt = buffer.indexOf('data', 36, 'ascii');
  const length = buffer.readUInt32LE(dataAt + 4) / 2;
  const sample = (i) => buffer.readInt16LE(dataAt + 8 + i * 2) / 32768;
  return { channels, rate, bits, length, seconds: length / rate, sample, bytes: buffer.length };
}

let totalBytes = 0;
for (const [id, file] of Object.entries(soundEffects)) {
  const wav = readWav(file);
  totalBytes += wav.bytes;
  check(wav.channels === 1 && wav.bits === 16, `${id}: mono 16-bit`);
  check(
    wav.seconds > 0.05 && wav.seconds <= 2.0,
    `${id}: a short, finite effect (${wav.seconds}s)`,
  );
  check(
    Math.abs(wav.seconds - soundDurations[id]) < 0.01,
    `${id}: duration table matches the file`,
  );
  check(
    Math.abs(wav.sample(0)) < 0.01 && Math.abs(wav.sample(wav.length - 1)) < 0.002,
    `${id}: starts and ends at silence (no click)`,
  );
}
for (const [id, file] of Object.entries(ambienceLoops)) {
  const wav = readWav(file);
  totalBytes += wav.bytes;
  check(wav.seconds >= 15 && wav.seconds <= 40, `${id} ambience: a long, quiet loop`);
  let steps = 0;
  for (let i = 1; i < wav.length; i++) steps += Math.abs(wav.sample(i) - wav.sample(i - 1));
  const typical = steps / (wav.length - 1);
  const seam = Math.abs(wav.sample(0) - wav.sample(wav.length - 1));
  check(seam < typical * 4, `${id} ambience: the loop joins without a seam`);
  let peak = 0;
  for (let i = 0; i < wav.length; i += 7) peak = Math.max(peak, Math.abs(wav.sample(i)));
  check(peak < 0.1, `${id} ambience: stays quiet (peak ${peak.toFixed(3)})`);
}
check(totalBytes < 2.5 * 1024 * 1024, `all sounds fit in 2.5 MB (${totalBytes} bytes)`);

// ------------------------------------------------------------------- engine
const soundSource = compile('lib/sound.ts');

/** A minimal Zustand substitute: getState, setState, subscribe and selector use. */
function create(init) {
  let state;
  const listeners = new Set();
  const set = (patch) => {
    state = { ...state, ...(typeof patch === 'function' ? patch(state) : patch) };
    for (const listener of listeners) listener(state);
  };
  state = init(set, () => state);
  const hook = (select) => select(state);
  hook.getState = () => state;
  hook.setState = set;
  hook.subscribe = (listener) => {
    listeners.add(listener);
    return () => listeners.delete(listener);
  };
  return hook;
}

function load({ os = 'web', saved = {}, activated = false, deferredSeeks = false } = {}) {
  const world = {
    now: 1000,
    storage: new Map(Object.entries(saved)),
    players: [],
    plays: [],
    pauses: [],
    modes: [],
    feedback: null,
    effects: [],
    handlers: new Map(),
    seeks: [],
  };
  const player = (source) => {
    const fake = {
      source,
      loop: false,
      currentTime: 0,
      play() {
        world.plays.push(source);
        fake.currentTime = 0.05;
      },
      pause() {
        world.pauses.push(source);
      },
      seekTo(seconds) {
        fake.currentTime = seconds;
        if (deferredSeeks) return new Promise((resolve) => world.seeks.push(resolve));
        return Promise.resolve();
      },
    };
    world.players.push(fake);
    return fake;
  };
  const destination = { exports: {} };
  const window = {
    addEventListener: (type, handler) => world.handlers.set(type, handler),
    removeEventListener: (type) => world.handlers.delete(type),
  };
  vm.runInNewContext(soundSource, {
    module: destination,
    exports: destination.exports,
    Date: { now: () => world.now },
    Promise,
    window: os === 'web' ? window : undefined,
    navigator: os === 'web' ? { userActivation: { hasBeenActive: activated } } : undefined,
    require(id) {
      if (id === 'react')
        return {
          useEffect(effect) {
            world.effects.push(effect());
          },
        };
      if (id === 'react-native') return { Platform: { OS: os } };
      if (id === '@react-native-async-storage/async-storage')
        return {
          __esModule: true,
          default: {
            getItem: async (key) => world.storage.get(key) ?? null,
            setItem: async (key, value) => world.storage.set(key, value),
          },
        };
      if (id === 'expo-audio')
        return {
          createAudioPlayer: player,
          setAudioModeAsync: async (mode) => world.modes.push(mode),
        };
      if (id === 'zustand') return { create };
      if (id === '@/lib/game')
        return {
          onFeedback(listener) {
            world.feedback = listener;
            return () => {
              world.feedback = null;
            };
          },
        };
      if (id === '@/lib/sound-assets') return assetsModule.exports;
      throw new Error(`Unexpected sound import: ${id}`);
    },
  });
  return { sound: destination.exports, world };
}
const settle = () => new Promise((resolve) => setImmediate(resolve));

async function main() {
  // Preferences: on by default, saved choices respected, nothing before load.
  {
    const { sound, world } = load({ activated: true });
    sound.playSound('tap');
    check(world.plays.length === 0, 'nothing plays before the saved preference is read');
    const stop = sound.startSound();
    await settle();
    const state = sound.useSoundPreference.getState();
    check(state.loaded && state.effects && state.ambience, 'effects and ambience default to on');
    sound.playSound('tap');
    check(world.plays.at(-1) === soundEffects.tap, 'a loaded, activated page plays effects');
    for (const kind of Object.keys(sound.feedbackSounds)) {
      world.now += 1000;
      world.feedback(kind);
      check(
        world.plays.at(-1) === soundEffects[sound.feedbackSounds[kind]],
        `the ${kind} cue plays its sound`,
      );
    }
    check(world.modes.length === 0, 'the web build leaves the native audio session alone');
    stop();
    check(world.feedback === null && world.handlers.size === 0, 'stopping removes all listeners');
  }
  {
    const { sound, world } = load({
      activated: true,
      saved: { 'napattack-sound-effects': 'false', 'napattack-sound-ambience': 'false' },
    });
    sound.startSound();
    await settle();
    sound.playSound('chime');
    sound.setAmbience('day');
    check(world.plays.length === 0, 'saved off settings keep effects and ambience silent');
    await sound.useSoundPreference.getState().setEffects(true);
    check(world.storage.get('napattack-sound-effects') === 'true', 'turning effects on is saved');
    sound.playSound('chime');
    check(world.plays.length === 1, 'effects play again once switched on');
    check(world.plays[0] === soundEffects.chime, 'the switched-on effect is the requested one');
    check(!world.plays.includes(ambienceLoops.day), 'ambience stays off on its own switch');
    await sound.useSoundPreference.getState().setAmbience(true);
    check(world.plays.at(-1) === ambienceLoops.day, 'turning ambience on resumes the garden loop');
  }

  // The web gesture gate: no audio until the page has been touched or keyed.
  {
    const { sound, world } = load();
    const stop = sound.startSound();
    await settle();
    sound.playSound('tap');
    sound.setAmbience('day');
    check(world.plays.length === 0, 'before a gesture the web build stays silent');
    world.handlers.get('pointerdown')();
    check(world.plays.at(-1) === ambienceLoops.day, 'the first tap starts the waiting ambience');
    const dayPlayer = world.players.find((fake) => fake.source === ambienceLoops.day);
    check(dayPlayer.loop === true, 'ambience players loop');
    sound.playSound('tap');
    check(world.plays.at(-1) === soundEffects.tap, 'after a gesture effects play');
    stop();
    check(world.pauses.includes(ambienceLoops.day), 'stopping sound pauses the ambience');
  }

  // Repeats, restarts and ambience switching.
  {
    const { sound, world } = load({ activated: true });
    sound.startSound();
    await settle();
    sound.playSound('tap');
    world.now += sound.REPEAT_MS - 1;
    sound.playSound('tap');
    check(world.plays.length === 1, 'a button and its cue in the same moment make one sound');
    world.now += 2;
    sound.playSound('tap');
    await settle();
    const tap = world.players.find((fake) => fake.source === soundEffects.tap);
    check(world.plays.length === 2 && tap.currentTime === 0.05, 'a later tap restarts from 0');
    check(
      world.players.filter((fake) => fake.source === soundEffects.tap).length === 1,
      'each effect reuses one player',
    );
    sound.setAmbience('day');
    sound.setAmbience('day');
    check(
      world.plays.filter((source) => source === ambienceLoops.day).length === 1,
      'asking for the same ambience again does not restart it',
    );
    sound.setAmbience('night');
    check(
      world.pauses.at(-1) === ambienceLoops.day && world.plays.at(-1) === ambienceLoops.night,
      'nightfall swaps the day loop for the night loop',
    );
    await sound.useSoundPreference.getState().setAmbience(false);
    check(world.pauses.at(-1) === ambienceLoops.night, 'switching ambience off pauses it at once');
    await sound.useSoundPreference.getState().setAmbience(true);
    check(world.plays.at(-1) === ambienceLoops.night, 'switching it back on resumes the loop');
    sound.useAmbience(null);
    const cleanup = world.effects.at(-1);
    check(world.pauses.at(-1) === ambienceLoops.night, 'a screen asking for no ambience stops it');
    sound.useAmbience('day');
    check(world.plays.at(-1) === ambienceLoops.day, 'a visible garden asks for its loop');
    world.effects.at(-1)();
    check(world.pauses.at(-1) === ambienceLoops.day, 'unmounting the garden stops its loop');
    check(typeof cleanup === 'function', 'the ambience hook always returns a cleanup');
  }

  // A deferred rewind must not outlive mute, cleanup, or a newer cue.
  for (const os of ['web', 'ios']) {
    for (const interruption of ['mute', 'stop', 'mute then unmute']) {
      const { sound, world } = load({ os, activated: true, deferredSeeks: true });
      const stop = sound.startSound();
      await settle();
      sound.playSound('tap');
      world.now += 1000;
      sound.playSound('tap');
      check(world.seeks.length === 1, `${os}: replay waits for rewind`);
      if (interruption === 'stop') stop();
      else {
        await sound.useSoundPreference.getState().setEffects(false);
        if (interruption === 'mute then unmute')
          await sound.useSoundPreference.getState().setEffects(true);
      }
      world.seeks[0]();
      await settle();
      check(world.plays.length === 1, `${os}: ${interruption} cancels deferred replay`);
      check(world.pauses.includes(soundEffects.tap), `${os}: ${interruption} stops active effects`);
      stop();
    }
    const { sound, world } = load({ os, activated: true, deferredSeeks: true });
    const stop = sound.startSound();
    await settle();
    sound.playSound('tap');
    world.now += 1000;
    sound.playSound('tap');
    world.now += 1000;
    sound.playSound('tap');
    check(world.plays.length === 2, `${os}: newer cue can play after the pending rewind`);
    world.seeks[0]();
    await settle();
    check(world.plays.length === 2, `${os}: older rewind cannot replay over the newer cue`);
    stop();
  }

  // Native: no gesture gate, and a polite audio session.
  {
    const { sound, world } = load({ os: 'ios' });
    const stop = sound.startSound();
    await settle();
    const mode = world.modes[0];
    check(
      mode?.interruptionMode === 'mixWithOthers' &&
        mode.playsInSilentMode === false &&
        mode.shouldPlayInBackground === false,
      'native sound mixes with music, obeys the silent switch and stops in the background',
    );
    sound.playSound('splash');
    check(world.plays.at(-1) === soundEffects.splash, 'native plays without a web gesture');
    stop();
  }
  console.log(
    `Sound: ${checks} checks passed (generated assets and the sound engine at its boundaries; no real audio output).`,
  );
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
