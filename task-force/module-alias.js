// module-alias.js
const moduleAlias = require('module-alias');
const path = require('path');

moduleAlias.addAlias('@', path.resolve(__dirname, 'src'));
