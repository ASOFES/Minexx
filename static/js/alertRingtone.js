/**
 * Sonnerie d'alerte MINEXX — modèle client-bar (Web Audio API).
 * Dual oscillator 880 + 660 Hz, boucle ~1.3s jusqu'à stopRingtone().
 */
(function (global) {
  'use strict';

  var STORAGE_KEY = 'minexx_call_alert';
  var audioCtx = null;
  var audioUnlocked = false;
  var ringInterval = null;
  var wakeLock = null;
  var ringing = false;

  function isEnabled() {
    try {
      var v = localStorage.getItem(STORAGE_KEY);
      if (v === null) return true;
      return v !== '0' && v !== 'false';
    } catch (e) {
      return true;
    }
  }

  function setEnabled(on) {
    try {
      localStorage.setItem(STORAGE_KEY, on ? '1' : '0');
    } catch (e) {}
  }

  function unlock() {
    return new Promise(function (resolve) {
      try {
        if (audioUnlocked && audioCtx && audioCtx.state === 'running') {
          resolve(true);
          return;
        }
        var AC = global.AudioContext || global.webkitAudioContext;
        if (!AC) {
          resolve(false);
          return;
        }
        if (!audioCtx) audioCtx = new AC();
        var done = function () {
          audioUnlocked = audioCtx.state === 'running';
          resolve(audioUnlocked);
        };
        if (audioCtx.state !== 'running') {
          audioCtx.resume().then(done).catch(function () { resolve(false); });
        } else {
          done();
        }
      } catch (e) {
        resolve(false);
      }
    });
  }

  function bindUnlockGestures() {
    var once = function () {
      unlock();
    };
    global.addEventListener('pointerdown', once, { once: true, passive: true });
    global.addEventListener('keydown', once, { once: true });
  }

  function stopRingtone() {
    ringing = false;
    try {
      if (ringInterval) {
        clearInterval(ringInterval);
        ringInterval = null;
      }
    } catch (e) {}
    try {
      if (wakeLock) {
        wakeLock.release && wakeLock.release();
        wakeLock = null;
      }
    } catch (e) {}
  }

  function ringOnce() {
    try {
      if (!audioCtx || audioCtx.state !== 'running') return;
      var osc1 = audioCtx.createOscillator();
      var osc2 = audioCtx.createOscillator();
      var gain = audioCtx.createGain();
      gain.gain.setValueAtTime(0.0001, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.6, audioCtx.currentTime + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + 0.9);
      osc1.type = 'sine';
      osc2.type = 'sine';
      osc1.frequency.setValueAtTime(880, audioCtx.currentTime);
      osc2.frequency.setValueAtTime(660, audioCtx.currentTime);
      osc1.connect(gain);
      osc2.connect(gain);
      gain.connect(audioCtx.destination);
      osc1.start();
      osc2.start();
      osc1.stop(audioCtx.currentTime + 0.95);
      osc2.stop(audioCtx.currentTime + 0.95);
      try {
        if (navigator.vibrate) {
          navigator.vibrate([300, 120, 300, 120, 300, 120, 300]);
        }
      } catch (e) {}
    } catch (e) {}
  }

  /**
   * @param {object} [opts]
   * @param {boolean} [opts.loop=true] — boucle jusqu'à stop (courses / assignation)
   * @param {number} [opts.maxMs] — arrêt auto après N ms (chat court)
   */
  function startRingtone(opts) {
    opts = opts || {};
    var loop = opts.loop !== false;
    var maxMs = opts.maxMs || 0;

    if (!isEnabled()) return Promise.resolve(false);

    return unlock().then(function (ok) {
      if (!ok) return false;
      stopRingtone();
      ringing = true;
      try {
        if (navigator.wakeLock && navigator.wakeLock.request) {
          navigator.wakeLock.request('screen').then(function (lock) {
            wakeLock = lock;
          }).catch(function () {});
        }
      } catch (e) {}

      ringOnce();
      if (loop) {
        ringInterval = setInterval(ringOnce, 1300);
        if (maxMs > 0) {
          setTimeout(function () {
            if (ringing) stopRingtone();
          }, maxMs);
        }
      }
      return true;
    });
  }

  /** Un seul bip (notifications douces). */
  function beepOnce() {
    return startRingtone({ loop: false });
  }

  /** Sonnerie urgente type course / assignation (boucle). */
  function ringUrgent() {
    return startRingtone({ loop: true });
  }

  /** Sonnerie chat : boucle courte ~6s puis stop. */
  function ringChat() {
    return startRingtone({ loop: true, maxMs: 6500 });
  }

  bindUnlockGestures();

  global.MinexxAlertRingtone = {
    unlock: unlock,
    startRingtone: startRingtone,
    stopRingtone: stopRingtone,
    beepOnce: beepOnce,
    ringUrgent: ringUrgent,
    ringChat: ringChat,
    isEnabled: isEnabled,
    setEnabled: setEnabled,
    isRinging: function () { return ringing; }
  };
})(typeof window !== 'undefined' ? window : this);
