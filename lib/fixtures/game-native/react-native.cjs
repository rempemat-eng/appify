exports.Platform = { OS: 'web' };
exports.AppState = {
  currentState: 'active',
  addEventListener() {
    return { remove() {} };
  },
};
exports.Vibration = { vibrate() {} };
