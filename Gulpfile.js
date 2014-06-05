var gulp = require("gulp"),
    $ = require("gulp-load-plugins")(),
    path = require("path");

var paths = {
  scripts: "assets/js/custom/**/*.js",
  images: "assets/images/**/*.{png,ico}",
  smileys: "assets/smileys/*",
  copy: ["assets/{css,js}/newsletter.{css,js}"],
  compass: {
    sass: "scss",
    images: "images",
    css: "css",
    project: path.join(__dirname, "assets/"),
    relative: false
  }
};

gulp.task("clean-compass", function() {
  return gulp.src(["assets/css/main.css", "assets/images/sprite{,@2x}-*.png"])
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
  return gulp.src("assets/scss/main.scss")
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
    .pipe($.imagemin())
    .pipe($.size())
    .pipe(gulp.dest("dist/images"));
});

gulp.task("smileys", function() {
  return gulp.src(paths.smileys)
    .pipe($.imagemin())
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

gulp.task("test", function() {
  return gulp.src(paths.scripts)
    .pipe($.jshint());
    //.pipe($.jshint.reporter("jshint-stylish")); <- quiet, since there is many errors
})

gulp.task("copy", function() {
  return gulp.src(paths.copy)
    .pipe(gulp.dest("dist/"));
});


gulp.task("build", ["smileys", "images", "stylesheet", "vendors", "script", "copy"]);

gulp.task("default", ["build"]);