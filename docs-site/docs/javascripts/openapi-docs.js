const REDOC_BUNDLE = "vendor/redoc.standalone.js";
const SWAGGER_BUNDLE = "vendor/swagger-ui-bundle.js";
const SWAGGER_STYLESHEET = "../stylesheets/vendor/swagger-ui.css";

function openApiDocsAssetUrl(relativePath) {
  const currentScript = document.querySelector('script[src$="javascripts/openapi-docs.js"]');
  if (currentScript && currentScript.src) {
    return new URL(relativePath, currentScript.src).toString();
  }
  return relativePath;
}

function loadScript(src) {
  return new Promise((resolve, reject) => {
    const existing = document.querySelector(`script[src="${src}"]`);
    if (existing) {
      if (existing.dataset.loaded === "true") {
        resolve();
        return;
      }
      existing.addEventListener("load", () => resolve(), { once: true });
      existing.addEventListener("error", () => reject(new Error(`Failed to load ${src}`)), { once: true });
      return;
    }

    const script = document.createElement("script");
    script.src = src;
    script.async = true;
    script.addEventListener("load", () => {
      script.dataset.loaded = "true";
      resolve();
    }, { once: true });
    script.addEventListener("error", () => reject(new Error(`Failed to load ${src}`)), { once: true });
    document.head.appendChild(script);
  });
}

function loadStylesheet(href) {
  if (document.querySelector(`link[href="${href}"]`)) {
    return;
  }
  const link = document.createElement("link");
  link.rel = "stylesheet";
  link.href = href;
  document.head.appendChild(link);
}

function initRedoc() {
  const container = document.getElementById("redoc-container");
  if (!container) {
    return;
  }

  const specUrl = new URLSearchParams(window.location.search).get("spec") || container.dataset.specUrl || "../openapi.yaml";
  loadScript(openApiDocsAssetUrl(REDOC_BUNDLE))
    .then(() => {
      if (!window.Redoc) {
        throw new Error("Redoc failed to initialize");
      }
      window.Redoc.init(
        specUrl,
        {
          hideDownloadButton: false,
          theme: {
            colors: {
              primary: {
                main: "#0b7c77"
              }
            },
            typography: {
              fontFamily: "Inter, sans-serif",
              headings: {
                fontFamily: "Inter, sans-serif"
              },
              code: {
                fontFamily: "JetBrains Mono, monospace"
              }
            }
          }
        },
        container
      );
    })
    .catch((error) => {
      container.innerHTML = `<p>Failed to load Redoc: ${error.message}</p>`;
    });
}

function initSwaggerUi() {
  const container = document.getElementById("swagger-ui");
  if (!container) {
    return;
  }

  const specUrl = new URLSearchParams(window.location.search).get("spec") || container.dataset.specUrl || "../openapi.yaml";
  loadStylesheet(openApiDocsAssetUrl(SWAGGER_STYLESHEET));
  loadScript(openApiDocsAssetUrl(SWAGGER_BUNDLE))
    .then(() => {
      if (!window.SwaggerUIBundle) {
        throw new Error("Swagger UI failed to initialize");
      }
      window.SwaggerUIBundle({
        url: specUrl,
        dom_id: "#swagger-ui",
        deepLinking: true,
        displayRequestDuration: true,
        presets: [window.SwaggerUIBundle.presets.apis],
        layout: "BaseLayout"
      });
    })
    .catch((error) => {
      container.innerHTML = `<p>Failed to load Swagger UI: ${error.message}</p>`;
    });
}

document.addEventListener("DOMContentLoaded", () => {
  initRedoc();
  initSwaggerUi();
});
