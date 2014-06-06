var gulp = require("gulp"),
    $ = require("gulp-load-plugins")(),
    path = require("path");
    lr = require("tiny-lr"),
    server = lr();

var paths = {
  scripts: "assets/js/**/*.js",
  images: "assets/images/**/*.{png,ico}",
  smileys: "assets/smileys/*",
  copy: ["assets/misc/**/*"],
  stylesheet: "assets/scss/main.scss",
  compass: {
    sass: "scss",
    images: "images",
    css: ".sass-css",
    project: path.join(__dirname, "assets/")
  }
};

gulp.task("clean-compass", function() {
  return gulp.src(["assets/.sass-css", "assets/images/sprite{,@2x}-*.png"])
    .pipe($.clean());
});

gulp.task("clean", ["clean-compass"], function() {
  return gulp.src(["dist/*"])
    .pipe($.clean());
});

gulp.task("script", ["test"], function() {
  return gulp.src(paths.scripts)
    .pipe($.concat("main.js", { newLine: "\r\n\r\n" }))
    .pipe(gulp.dest("dist/js"))
    .pipe($.size({ title: "main.js" }))
    .pipe($.rename({ suffix: ".min" }))
    .pipe($.uglify())
    .pipe(gulp.dest("dist/js"))
    .pipe($.size({ title: "main.min.js" }));
});

gulp.task("stylesheet", function() {
  return gulp.src(paths.stylesheet)
    .pipe($.compass({
      project: paths.compass.project,
      css: paths.compass.css,
      sass: paths.compass.sass,
      image: paths.compass.images
    }))
    .pipe(gulp.dest("dist/css"))
    .pipe($.rename({ suffix: ".min" })) // génère une version minimifié
    .pipe($.minifyCss())
    .pipe(gulp.dest("dist/css"));
});

gulp.task("images", ["stylesheet"], function() {
  return gulp.src(paths.images)
    .pipe($.cache($.imagemin({ optimizationLevel: 3, progressive: true, interlaced: true })))
    .pipe($.size())
    .pipe(gulp.dest("dist/images"));
});

gulp.task("smileys", function() {
  return gulp.src(paths.smileys)
    .pipe($.cache($.imagemin({ optimizationLevel: 3, progressive: true, interlaced: true })))
    .pipe($.size())
    .pipe(gulp.dest("dist/smileys"));
});

gulp.task("vendors", function() {
  return $.bowerFiles()
    .pipe($.flatten()) // remove folder structure
    .pipe($.size({ title: "vendors", showFiles: true }))
    .pipe(gulp.dest("dist/js/vendors"))
    .pipe($.concat("vendors.js"))
    .pipe($.size({ title: "vendors.js" }))
    .pipe(gulp.dest("dist/js"))
    .pipe($.uglify())
    .pipe($.rename("vendors.min.js"))
    .pipe($.size({ title: "vendors.min.js" }))
    .pipe(gulp.dest("dist/js"));
});

gulp.task("merge-scripts", ["script", "vendors"], function() {
  return gulp.src("dist/js/{vendors,main}.min.js")
    .pipe($.concat("all.min.js"))
    .pipe($.size())
    .pipe(gulp.dest("dist/js/"));
});

gulp.task("watch", function() {
  gulp.watch(paths.script, ["script"]);
  gulp.watch(paths.copy, ["copy"]);
  gulp.watch(paths.smiley, ["smileys"]);
  gulp.watch(paths.imafes, ["images"]);
  gulp.watch(paths.stylesheet, ["stylesheet"]);
});

gulp.task("test", function() {
  return gulp.src(paths.scripts)
    .pipe($.jshint());
    //.pipe($.jshint.reporter("jshint-stylish")); <- quiet, since there is many errors
});

gulp.task("copy", function() {
  return gulp.src(paths.copy)
    .pipe(gulp.dest("dist/"));
});

gulp.task("travis", function() {
  // @TODO: Configure travis tests
  return true;
});


gulp.task("build", ["smileys", "images", "stylesheet", "vendors", "script", "merge-scripts", "copy"]);

gulp.task("default", ["build"]);