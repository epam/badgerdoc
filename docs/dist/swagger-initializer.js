window.onload = function () {
  //<editor-fold desc="Changeable Configuration Block">
  // ./specs-list.json contains list of services' openapi specs
  const urls = fetch("./specs-list.json");
  
  urls.then((response) => response.json()).then((data) => {
    window.ui = SwaggerUIBundle({
      urls: data,
      dom_id: '#swagger-ui',
      deepLinking: true,
      presets: [
        SwaggerUIBundle.presets.apis,
        SwaggerUIStandalonePreset
      ],
      plugins: [
        SwaggerUIBundle.plugins.DownloadUrl
      ],
      layout: "StandaloneLayout"
    });
  });
  //</editor-fold>
};
