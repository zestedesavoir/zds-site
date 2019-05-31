const path = require('path');
const livereload = require('gulp-livereload');
const concat = require('gulp-concat');
const del = require('del');
const gulp = require('gulp');
const gulpif = require('gulp-if');
const imagemin = require('gulp-imagemin');
const postcss = require('gulp-postcss');
const sass = require('gulp-sass');
const sourcemaps = require('gulp-sourcemaps');
const spritesmith = require('gulp.spritesmith');
const uglify = require('gulp-uglify');
const jshint = require('gulp-jshint');
const options = require('gulp-options');
const autoprefixer = require('autoprefixer');
const cssnano = require('cssnano');
const fs = require('fs');

const fast = options.has("speed");

//>> PostCSS plugins used
const postcssPlugins = [
    autoprefixer({ browsers: ['last 2 versions', '> 1%', 'ie >= 9'] })
];

if (!fast) {
    postcssPlugins.push(cssnano());
    console.log("The speed mode is not enabled.");
} else {
    console.log("The speed mode is enabled.");
}
//<<

const customSass = () => sass({
    sourceMapContents: true,
    includePaths: [
        path.join(__dirname, 'node_modules'),
        path.join(__dirname, 'dist', 'scss'),
    ],
});

// Deletes the generated files
gulp.task('clean', () => del([
    'dist/',
]));

// Lint the js source files
gulp.task('js:lint', () =>
    gulp.src([
        'assets/js/*.js',
        '!assets/js/editor.js', // We'll fix that later
    ])
        .pipe(jshint())
        .pipe(jshint.reporter('jshint-stylish'))
        .pipe(jshint.reporter('fail')));

// Concat and minify all the js files
gulp.task('js', () =>
    gulp.src([
        require.resolve('jquery'),
        require.resolve('cookies-eu-banner'),
        require.resolve('moment/moment.js'),
        require.resolve('moment/locale/fr.js'),
        require.resolve('chart.js/dist/Chart.js'),
        // Used by other scripts, must be first
        'assets/js/modal.js',
        'assets/js/tooltips.js',

        'assets/js/accessibility-links.js',
        'assets/js/accordeon.js',
        'assets/js/ajax-actions.js',
        'assets/js/autocompletion.js',
        'assets/js/charts.js',
        'assets/js/close-alert-box.js',
        'assets/js/compare-commits.js',
        'assets/js/content-export.js',
        'assets/js/content-publication-readiness.js',
        'assets/js/dropdown-menu.js',
        'assets/js/editor.js',
        'assets/js/editor-persistence.js',
        'assets/js/featured-resource-preview.js',
        'assets/js/form-email-username.js',
        'assets/js/gallery.js',
        'assets/js/index.js',
        'assets/js/jquery-tabbable.js',
        'assets/js/karma.js',
        'assets/js/keyboard-navigation.js',
        'assets/js/markdown-help.js',
        'assets/js/message-hidden.js',
        'assets/js/message-signature.js',
        'assets/js/mobile-menu.js',
        'assets/js/select-autosubmit.js',
        'assets/js/snow.js',
        'assets/js/spoiler.js',
        'assets/js/submit-dbclick.js',
        'assets/js/tab-modalize.js',
        'assets/js/topic-suggest.js',
        'assets/js/tribune-pick.js',
        'assets/js/zen-mode.js',
    ], { base: '.' })
        .pipe(sourcemaps.init({ loadMaps: true }))
        .pipe(concat('script.js', { newline: ';\r\n' }))
        .pipe(gulpif(!fast, uglify()))
        .on('error', function (err) {
            // gulp-uglify sucks
            console.log(err.toString());
        })
        .pipe(sourcemaps.write('.', { includeContent: true, sourceRoot: '../../' }))
        .pipe(gulp.dest('dist/js/')));

katexFolder = 'zmd'
if(fs.existsSync('/opt/zmd')) {
    katexFolder = '/opt/zmd'
}

gulp.task('prepare-zmd', () =>
    gulp.src([katexFolder + '/node_modules/katex/dist/{katex.min.css,fonts/*}'])
        .pipe(gulp.dest('dist/css/')));

// Compiles the SCSS files to CSS
gulp.task('css', ['css:sprite'], () =>
    gulp.src(['assets/scss/main.scss', 'assets/scss/zmd.scss'])
        .pipe(sourcemaps.init())
        .pipe(customSass())
        .pipe(gulpif(!fast, postcss(postcssPlugins)))
        .pipe(sourcemaps.write('.', { includeContent: true, sourceRoot: '../../assets/scss/' }))
        .pipe(gulp.dest('dist/css/')));

// Generates a sprite
gulp.task('css:sprite', () =>
    gulp.src('assets/images/sprite/*.png')
        .pipe(spritesmith({
            cssTemplate: 'assets/scss/_sprite.scss.hbs',
            cssName: 'scss/_sprite.scss',
            imgName: 'images/sprite.png',
            retinaImgName: 'images/sprite@2x.png',
            retinaSrcFilter: 'assets/images/sprite/*@2x.png',
        }))
        .pipe(gulp.dest('dist/')));

// Optimizes the images
gulp.task('images', ['css:sprite'], () =>
    gulp.src('assets/{images,smileys,licenses}/**/*')
        .pipe(gulpif(!fast, imagemin()))
        .pipe(gulp.dest('dist/'))
);

// Watch for file changes
gulp.task('watch-runner', () => {
    gulp.watch('assets/js/*.js', ['js']);
    gulp.watch(['assets/{images,smileys}/**/*', '!assets/images/sprite*.png'], ['images']);
    gulp.watch(['assets/scss/**/*.scss', '!assets/scss/_sprite.scss'], ['css']);

    gulp.watch('dist/**/*', file =>
         livereload.changed(
            path.join('static/', path.relative(path.join(__dirname, 'dist/'), file.path))
        )
    );

    livereload.listen();
});

// https://github.com/gulpjs/gulp/issues/259#issuecomment-152177973
gulp.task('watch', cb => {
    function spawnGulp(args) {
        if (fast)
            args.push("--speed");
        return require('child_process')
            .spawn(
                'node_modules/.bin/gulp',
                args,
                {stdio: 'inherit'}
            )
    }

    function spawnBuild() {
        return spawnGulp(['build'])
            .on('close', spawnWatch)
    }

    function spawnWatch() {
        return spawnGulp(['watch-runner'])
            .on('close', spawnWatch)
    }

    spawnBuild();
});

// Compiles errors' CSS
gulp.task('errors', () =>
    gulp.src('errors/scss/main.scss')
        .pipe(sourcemaps.init())
        .pipe(customSass())
        .pipe(gulpif(!fast, postcss(postcssPlugins)))
        .pipe(sourcemaps.write('.', { includeContent: true, sourceRoot: '../scss/' }))
        .pipe(gulp.dest('errors/css/')));

gulp.task('build', ['prepare-zmd', 'css', 'js', 'images']);
gulp.task('default', ['watch', 'js:lint']);
