// Import all javascript files to bundle them into a single one

// ZDSAjax library
import ZDSAjax from "../assets/js/common/ajax";
window.ajax = new ZDSAjax();

// Other modules
import.meta.glob([
    "../assets/js/common/*.js",
    "../assets/js/*.js",
  ], { eager: true, import: 'default' });
