const REDOC_BUNDLE = "vendor/redoc.standalone.js";
const SWAGGER_BUNDLE = "vendor/swagger-ui-bundle.js";
const SWAGGER_STYLESHEET = "../stylesheets/vendor/swagger-ui.css";

function openApiDocsAssetUrl(relativePath) {
  const currentScript = document.querySelector('script[src*="javascripts/openapi-docs.js"]');
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

function applyOpenApiPageLayout(container, pageClass) {
  if (!container) {
    return;
  }

  document.body.classList.add("openapi-reference-page", pageClass);

  const article = container.closest(".md-content__inner");
  if (article) {
    article.classList.add("openapi-reference-article");
  }
}

function resetOpenApiPageLayout() {
  document.body.classList.remove("openapi-reference-page", "openapi-reference-page--redoc", "openapi-reference-page--swagger");
  document.querySelectorAll(".openapi-reference-article").forEach((article) => {
    article.classList.remove("openapi-reference-article");
  });
}

function openApiSpecUrl(container) {
  const specUrl = new URLSearchParams(window.location.search).get("spec") || container.dataset.specUrl || "../openapi.yaml";
  return new URL(specUrl, window.location.href).toString();
}

function initRedoc() {
  const container = document.getElementById("redoc-container");
  if (!container) {
    return;
  }

  applyOpenApiPageLayout(container, "openapi-reference-page--redoc");

  const specUrl = openApiSpecUrl(container);
  if (container.dataset.openapiInitialized === specUrl) {
    return;
  }
  container.dataset.openapiInitialized = specUrl;
  container.innerHTML = "";

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
      container.dataset.openapiInitialized = "";
      container.innerHTML = `<p>Failed to load Redoc: ${error.message}</p>`;
    });
}

function initSwaggerUi() {
  const container = document.getElementById("swagger-ui");
  if (!container) {
    return;
  }

  applyOpenApiPageLayout(container, "openapi-reference-page--swagger");

  const specUrl = openApiSpecUrl(container);
  if (container.dataset.openapiInitialized === specUrl) {
    return;
  }
  container.dataset.openapiInitialized = specUrl;
  container.innerHTML = "";

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
      container.dataset.openapiInitialized = "";
      container.innerHTML = `<p>Failed to load Swagger UI: ${error.message}</p>`;
    });
}

function initOpenApiDocs() {
  const hasOpenApiReference = document.getElementById("redoc-container") || document.getElementById("swagger-ui");
  resetOpenApiPageLayout();
  if (!hasOpenApiReference) {
    return;
  }
  initRedoc();
  initSwaggerUi();
}

if (window.document$ && typeof window.document$.subscribe === "function") {
  window.document$.subscribe(() => initOpenApiDocs());
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initOpenApiDocs, { once: true });
} else {
  initOpenApiDocs();
}
