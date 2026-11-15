import { getAuth } from "@/lib/auth/server";

type AuthMethod = "GET" | "POST" | "PUT" | "DELETE" | "PATCH";
type RouteHandler = (...args: any[]) => Response | Promise<Response>;

function createRouteHandler(method: AuthMethod): RouteHandler {
  return async (...args: any[]) => {
    const auth = getAuth();
    if (!auth) {
      return Response.json({ error: "auth_not_configured" }, { status: 503 });
    }

    const handlers = auth.handler();
    const handler = handlers[method] as RouteHandler;
    return handler.apply(handlers, args);
  };
}

export const GET = createRouteHandler("GET");
export const POST = createRouteHandler("POST");
export const PUT = createRouteHandler("PUT");
export const DELETE = createRouteHandler("DELETE");
export const PATCH = createRouteHandler("PATCH");
