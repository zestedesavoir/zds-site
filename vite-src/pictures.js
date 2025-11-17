// Dynamically import all images inside the 'assets/images' directory

const pngAssets = import.meta.glob([
  "../assets/images/**/*.png",
  "!../assets/images/sprite/*.png",
  "../assets/smileys/**/*.png",
  "../assets/licenses/**/*.png",
], { eager: true, import: 'default', query:'?url' });

const svgAssets = import.meta.glob([
  "../assets/images/**/*.svg",
  "!../assets/images/sprite/*.svg",
  "../assets/smileys/**/*.svg",
  "../assets/licenses/**/*.svg",
], { eager: true, import: 'default', query:'?url' });

const gifAssets = import.meta.glob([
  "../assets/images/**/*.gif",
  "!../assets/images/sprite/*.gif",
  "../assets/smileys/**/*.gif",
  "../assets/licenses/**/*.gif",
], { eager: true, import: 'default', query:'?url' });

const appTag = document.querySelector('#app');

appTag.innerHTML += Object.keys(pngAssets).reduce((accumulatedhtml, pngAssetUrl) => accumulatedhtml +
  `<img src="${pngAssets[pngAssetUrl]}"/>`, "");

appTag.innerHTML += Object.keys(svgAssets).reduce((accumulatedhtml, svgAssetUrl) => accumulatedhtml +
  `<img src="${svgAssets[svgAssetUrl]}"/>`, "");

appTag.innerHTML += Object.keys(gifAssets).reduce((accumulatedhtml, gifAssetUrl) => accumulatedhtml +
  `<img src="${gifAssets[gifAssetUrl]}"/>`, "");
