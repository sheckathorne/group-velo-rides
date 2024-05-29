const path = require("path");
const BundleTracker = require("webpack-bundle-tracker");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");

module.exports = {
  target: "web",
  context: path.join(__dirname, "../"),
  entry: {
    project: path.resolve(__dirname, "../group_velo/static/js/project"),
    vendors: path.resolve(__dirname, "../group_velo/static/js/vendors"),
    createEvent: path.resolve(__dirname, "../group_velo/static/js/createEvent"),
    messaging: path.resolve(__dirname, "../group_velo/static/js/messaging"),
    modifyEvent: path.resolve(__dirname, "../group_velo/static/js/modifyEvent"),
    rideLayout: path.resolve(__dirname, "../group_velo/static/js/rideLayout"),
    myRoutes: path.resolve(__dirname, "../group_velo/static/js/myRoutes"),
    createClub: path.resolve(__dirname, "../group_velo/static/js/createClub"),
    createRoute: path.resolve(__dirname, "../group_velo/static/js/createRoute"),
    clubSearch: path.resolve(__dirname, "../group_velo/static/js/clubSearch"),
    rideFilter: path.resolve(__dirname, "../group_velo/static/js/rideFilter"),
    editProfile: path.resolve(__dirname, "../group_velo/static/js/editProfile"),
    userNotifications: path.resolve(
      __dirname,
      "../group_velo/static/js/userNotifications",
    ),
  },
  output: {
    path: path.resolve(__dirname, "../group_velo/static/webpack_bundles/"),
    publicPath: "/static/webpack_bundles/",
    filename: "js/[name]-[fullhash].js",
    chunkFilename: "js/[name]-[hash].js",
    library: "GroupVeloUtils",
    libraryTarget: "umd",
  },
  plugins: [
    new BundleTracker({
      path: path.resolve(path.join(__dirname, "../")),
      filename: "webpack-stats.json",
    }),
    new MiniCssExtractPlugin({ filename: "css/[name].[contenthash].css" }),
  ],
  module: {
    rules: [
      // we pass the output from babel loader to react-hot loader
      {
        test: /\.js$/,
        loader: "babel-loader",
      },
      {
        test: /\.s?css$/i,
        use: [
          MiniCssExtractPlugin.loader,
          "css-loader",
          {
            loader: "postcss-loader",
            options: {
              postcssOptions: {
                plugins: ["postcss-preset-env", "autoprefixer", "pixrem"],
              },
            },
          },
          "sass-loader",
        ],
      },
    ],
  },
  resolve: {
    modules: ["node_modules"],
    extensions: [".js", ".jsx"],
  },
};
