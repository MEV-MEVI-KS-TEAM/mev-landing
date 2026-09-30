// Carril TikTok: entrega el pixel "MEV TT" SOLO a las páginas de /tt.
// El ID vive en la variable de entorno NEXT_PUBLIC_TIKTOK_PIXEL_ID (Netlify, contextos
// production y deploy-preview) y no en el código. Si falta o no parece un ID de TikTok,
// responde un script vacío: /tt no carga el pixel y no truena (los ttq.track() de la
// página quedan en la cola del código base y nadie los envía).
export default async () => {
  const id = (Netlify.env.get("NEXT_PUBLIC_TIKTOK_PIXEL_ID") || "").trim();
  const body = /^[A-Z0-9]{8,32}$/.test(id)
    ? `(function(){var t=window.ttq;if(!t||typeof t.load!=="function")return;t.load(${JSON.stringify(id)});t.page();})();\n`
    : "/* Pixel de TikTok desactivado: falta NEXT_PUBLIC_TIKTOK_PIXEL_ID */\n";
  return new Response(body, {
    headers: {
      "content-type": "application/javascript; charset=utf-8",
      "cache-control": "public, max-age=300",
    },
  });
};

export const config = { path: "/tt/pixel.js" };
