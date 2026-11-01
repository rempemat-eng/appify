const { randomBytes, randomUUID } = require('node:crypto');

exports.randomUUID = randomUUID;
exports.getRandomBytes = function (size) {
  return new Uint8Array(randomBytes(size));
};
