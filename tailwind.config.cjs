module.exports = {
  content: ["./group_velo/templates/**/*.html", "./group_velo/**/*.py"],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter var"],
      },
    },
  },
  plugins: [
    require("autoprefixer"),
    require("@tailwindcss/forms")({
      strategy: "class",
    }),
  ],
};
