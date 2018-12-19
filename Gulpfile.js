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

// >> gulp dependencies
const log = require('fancy-log');
const color = require('ansi-colors');
// <<

const fast = options.has("speed");
const fixSFTP = options.has("fixsftp");

// PostCSS plugins used
const postcssPlugins = [
    autoprefixer({ browsers: ['last 2 versions', '> 1%', 'ie >= 9'] })
];

if (!fast) {
    postcssPlugins.push(cssnano());
    log(color.green("The speed mode is not enabled."));
} else {
    log(color.green("The speed mode is enabled."));
}

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
        'assets/js/content-publication-readiness.js',
        'assets/js/dropdown-menu.js',
        'assets/js/editor.js',
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
            log(color.red(err.toString()));
        })
        .pipe(sourcemaps.write('.', { includeContent: true, sourceRoot: '../../' }))
        .pipe(gulp.dest('dist/js/')));

gulp.task('prepare-zmd', () =>
    gulp.src(['node_modules/katex/dist/{katex.min.css,fonts/*}'])
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

// >> fixSFTP
const denyRules = {};
let showMsgNextTime = false;
function onChangeTimeout(taskName, path) {
    timeout = denyRules[taskName][path];

    if (timeout) {
        showMsgNextTime && log(`Waiting file for '${color.cyan(taskName)}' ${color.magenta(path)}`);

        process.stdout.write(".");
        clearTimeout(timeout);
        
        showMsgNextTime = false;
    } else {
        showMsgNextTime = true;
    }

    startWithTimeout(taskName, path);
}

function startWithTimeout(taskName, path) {
    denyRules[taskName][path] = setTimeout((taskName) => {
        process.stdout.write(".\n");
        gulp.start(taskName);
        denyRules[taskName][path] = false;
    }, 1500, taskName);  
}   // ^^^^-> 1.5 sec
// << 

// Watch for file changes
gulp.task('watch-runner', () => {
    const watchlist = {
        js: 'assets/js/*.js',
        images: ['assets/{images,smileys}/**/*', '!assets/images/sprite*.png'],
        css: ['assets/scss/**/*.scss', '!assets/scss/_sprite.scss']
    };

    fixSFTP && log(color.green("The fixSFTP is enabled."));

    Object.keys(watchlist).forEach((taskName) => {
        let src = watchlist[taskName];
        if (fixSFTP) {
            let watcher = gulp.watch(src);
            watcher.on("change", (event) => onChangeTimeout(taskName, event.path));
            /*                    ^^^^^
                WARNING: In Gulp 4.0, `(event)` will be replaced by `(path, stats)`
                current doc : https://github.com/gulpjs/gulp/blob/v3.9.1/docs/API.md#tasks
            */
            denyRules[taskName] = {};
        } else {
            gulp.watch(src, [ taskName ])
        }
    });

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
        if (fixSFTP)
            args.push("--fixsftp");
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

gulp.task('test', ['js:lint']);
gulp.task('build', ['prepare-zmd', 'css', 'js', 'images']);
gulp.task('default', ['watch', 'test']);
