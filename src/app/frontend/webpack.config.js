
const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');

module.exports = {
  entry: './dashboard.js',
  output: {
    filename: 'bundle.js',
    path: path.resolve(__dirname, '../static'),
  },
  plugins: [
    new HtmlWebpackPlugin({
      template: '../dashboard.html',
      filename: '../dashboard.html'
    }),
  ],
  mode: 'production',
};
