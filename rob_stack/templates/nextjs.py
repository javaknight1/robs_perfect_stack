"""Next.js (Vercel) project templates."""

import json


def generate_nextjs(root, ctx: dict, write) -> None:
    name = ctx["name"]
    title = ctx["title"]
    schema = ctx["schema"]

    print("\n📦 Generating Next.js app...")

    write(root, "package.json",         _package_json(name))
    write(root, "next.config.ts",       _next_config())
    write(root, "tsconfig.json",        _tsconfig())
    write(root, "tailwind.config.ts",   _tailwind_config())
    write(root, "middleware.ts",        _middleware())
    write(root, "vercel.json",          _vercel_json())
    write(root, ".env.example",         _env_example(name, schema))
    write(root, "src/app/layout.tsx",   _layout(title))
    write(root, "src/app/page.tsx",     _page())
    write(root, "src/app/globals.css",  "@import \"tailwindcss\";\n")
    write(root, "src/components/providers.tsx", _providers())
    write(root, "src/lib/supabase.ts",  _lib_supabase(schema))
    write(root, "src/lib/redis.ts",     _lib_redis())
    write(root, "src/lib/resend.ts",    _lib_resend(title))
    write(root, "src/lib/r2.ts",        _lib_r2())
    write(root, "src/lib/posthog.ts",   _lib_posthog())
    write(root, "src/app/(auth)/sign-in/[[...sign-in]]/page.tsx", _sign_in_page())
    write(root, "src/app/(auth)/sign-up/[[...sign-up]]/page.tsx", _sign_up_page())
    write(root, "src/app/(auth)/layout.tsx", _auth_layout())
    write(root, "instrumentation.ts",  _instrumentation())
    write(root, "src/app/dashboard/page.tsx", _dashboard_page())
    write(root, "postcss.config.mjs",  _postcss_config())
    write(root, "src/app/api/health/route.ts", _health_route())
    write(root, "eslint.config.mjs",  _eslint_config())
    write(root, "src/emails/welcome.tsx", _welcome_email())
    write(root, "src/lib/swagger.ts",  _swagger_config(title))
    write(root, "src/app/api-docs/page.tsx", _api_doc_page())
    write(root, "src/app/api/docs/route.ts", _openapi_route())
    write(root, "Makefile",            _makefile_nextjs())


# ───────────────────────────────���──────────────────────────────────

def _package_json(name: str) -> str:
    return json.dumps({
        "name": name,
        "version": "0.1.0",
        "private": True,
        "scripts": {
            "dev": "next dev",
            "build": "next build",
            "start": "next start",
            "lint": "next lint",
        },
        "dependencies": {
            "next": "^15",
            "react": "^19",
            "react-dom": "^19",
            "@clerk/nextjs": "^6",
            "@supabase/supabase-js": "^2",
            "@upstash/redis": "^1",
            "resend": "^4",
            "@aws-sdk/client-s3": "^3",
            "@aws-sdk/s3-request-presigner": "^3",
            "posthog-js": "^1",
            "posthog-node": "^4",
            "@sentry/nextjs": "^8",
            "@react-email/components": "^0",
            "next-swagger-doc": "^0",
            "swagger-ui-react": "^5",
        },
        "devDependencies": {
            "typescript": "^5",
            "@types/node": "^22",
            "@types/react": "^19",
            "@types/react-dom": "^19",
            "@types/swagger-ui-react": "^4",
            "tailwindcss": "^4",
            "@tailwindcss/postcss": "^4",
            "eslint": "^9",
            "eslint-config-next": "^15",
            "@eslint/eslintrc": "^3",
        },
    }, indent=2)


def _next_config() -> str:
    return '''\
import { withSentryConfig } from "@sentry/nextjs";

/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: { instrumentationHook: true },
};

export default withSentryConfig(nextConfig, {
  org: process.env.SENTRY_ORG,
  project: process.env.SENTRY_PROJECT,
  silent: !process.env.CI,
  widenClientFileUpload: true,
  hideSourceMaps: true,
  disableLogger: true,
});
'''


def _tsconfig() -> str:
    return json.dumps({
        "compilerOptions": {
            "target": "ES2017",
            "lib": ["dom", "dom.iterable", "esnext"],
            "allowJs": True,
            "skipLibCheck": True,
            "strict": True,
            "noEmit": True,
            "esModuleInterop": True,
            "module": "esnext",
            "moduleResolution": "bundler",
            "resolveJsonModule": True,
            "isolatedModules": True,
            "jsx": "preserve",
            "incremental": True,
            "plugins": [{"name": "next"}],
            "paths": {"@/*": ["./src/*"]},
        },
        "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
        "exclude": ["node_modules"],
    }, indent=2)


def _tailwind_config() -> str:
    return '''\
import type { Config } from "tailwindcss";

export default {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: { extend: {} },
  plugins: [],
} satisfies Config;
'''


def _middleware() -> str:
    return '''\
import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

const isPublicRoute = createRouteMatcher([
  "/",
  "/sign-in(.*)",
  "/sign-up(.*)",
  "/api/webhooks(.*)",
  "/api-docs(.*)",
  "/api/docs(.*)",
]);

export default clerkMiddleware(async (auth, req) => {
  if (!isPublicRoute(req)) await auth.protect();
});

export const config = {
  matcher: [
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    "/(api|trpc)(.*)",
  ],
};
'''


def _vercel_json() -> str:
    return json.dumps({
        "framework": "nextjs",
        "buildCommand": "next build",
        "devCommand": "next dev",
        "installCommand": "npm install",
    }, indent=2)


def _env_example(name: str, schema: str) -> str:
    return f"""\
# ── Supabase ──────────────────────────────────────────────────────
SUPABASE_URL=https://PROJECT.supabase.co
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
# Schema-scoped connection — only {schema} schema is accessible
DATABASE_URL=postgresql://{schema}_app:PASSWORD@db.PROJECT.supabase.co:5432/postgres?search_path={schema}

# ── Upstash Redis ─────────────────────────────────────────────────
UPSTASH_REDIS_REST_URL=https://YOUR.upstash.io
UPSTASH_REDIS_REST_TOKEN=

# ── Clerk ─────────────────────────────────────────────────────────
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_
CLERK_SECRET_KEY=sk_test_
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/dashboard
NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/dashboard

# ── Resend ────────────────────────────────────────────────────────
RESEND_API_KEY=re_
RESEND_FROM_EMAIL=noreply@yourdomain.com

# ── Cloudflare R2 ─────────────────────────────────────────────────
R2_ACCOUNT_ID=
R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=
R2_BUCKET_NAME={name}
R2_PUBLIC_URL=https://pub-XXXX.r2.dev

# ── PostHog ───────────────────────────────────────────────────────
NEXT_PUBLIC_POSTHOG_KEY=phc_
NEXT_PUBLIC_POSTHOG_HOST=https://us.i.posthog.com

# ── Sentry ────────────────────────────────────────────────────────
SENTRY_DSN=https://
NEXT_PUBLIC_SENTRY_DSN=https://
SENTRY_ORG=
SENTRY_PROJECT=

# ── BetterStack ───────────────────────────────────────────────────
BETTERSTACK_SOURCE_TOKEN=
"""


def _layout(title: str) -> str:
    return f'''\
import type {{ Metadata }} from "next";
import {{ ClerkProvider }} from "@clerk/nextjs";
import {{ PostHogProvider }} from "@/components/providers";
import "./globals.css";

export const metadata: Metadata = {{
  title: "{title}",
  description: "{title} — built on Rob\\'s stack",
}};

export default function RootLayout({{ children }}: {{ children: React.ReactNode }}) {{
  return (
    <ClerkProvider>
      <html lang="en">
        <body>
          <PostHogProvider>{{children}}</PostHogProvider>
        </body>
      </html>
    </ClerkProvider>
  );
}}
'''


def _page() -> str:
    return '''\
import { auth } from "@clerk/nextjs/server";

export default async function Home() {
  const { userId } = await auth();
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <h1 className="text-4xl font-bold">Welcome</h1>
      {userId ? (
        <p className="mt-4 text-gray-500">Signed in as {userId}</p>
      ) : (
        <p className="mt-4 text-gray-500">
          <a href="/sign-in" className="underline">Sign in</a> to get started.
        </p>
      )}
    </main>
  );
}
'''


def _providers() -> str:
    return '''\
"use client";

import posthog from "posthog-js";
import { PostHogProvider as PHProvider } from "posthog-js/react";
import { useEffect } from "react";
import { usePathname, useSearchParams } from "next/navigation";

function PostHogPageview() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  useEffect(() => {
    if (pathname && posthog) {
      let url = window.origin + pathname;
      if (searchParams.toString()) url += "?" + searchParams.toString();
      posthog.capture("$pageview", { "$current_url": url });
    }
  }, [pathname, searchParams]);
  return null;
}

export function PostHogProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
      api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST,
      person_profiles: "identified_only",
      capture_pageview: false,
    });
  }, []);
  return (
    <PHProvider client={posthog}>
      <PostHogPageview />
      {children}
    </PHProvider>
  );
}
'''


def _lib_supabase(schema: str) -> str:
    return f'''\
import {{ createClient }} from "@supabase/supabase-js";

const URL   = process.env.SUPABASE_URL!;
const ANON  = process.env.SUPABASE_ANON_KEY!;
const SCHEMA = "{schema}";

// Server-side admin client (bypasses RLS)
export const supabaseAdmin = createClient(URL, process.env.SUPABASE_SERVICE_ROLE_KEY!, {{
  db: {{ schema: SCHEMA }},
}});

// Client-side client (respects RLS)
export const supabase = createClient(URL, ANON, {{
  db: {{ schema: SCHEMA }},
}});
'''


def _lib_redis() -> str:
    return '''\
import { Redis } from "@upstash/redis";

export const redis = new Redis({
  url:   process.env.UPSTASH_REDIS_REST_URL!,
  token: process.env.UPSTASH_REDIS_REST_TOKEN!,
});

export const getCache  = <T>(key: string) => redis.get<T>(key);
export const setCache  = <T>(key: string, value: T, ex = 3600) => redis.set(key, value, { ex });
export const delCache  = (key: string) => redis.del(key);
'''


def _lib_resend(title: str) -> str:
    return f'''\
import {{ Resend }} from "resend";

export const resend = new Resend(process.env.RESEND_API_KEY);

const APP  = "{title}";
const FROM = process.env.RESEND_FROM_EMAIL ?? "noreply@yourdomain.com";

export async function sendEmail({{
  to, subject, html, text,
}}: {{
  to: string | string[];
  subject: string;
  html: string;
  text?: string;
}}) {{
  const {{ data, error }} = await resend.emails.send({{
    from: `${{APP}} <${{FROM}}>`,
    to, subject, html, text,
  }});
  if (error) throw new Error(`Resend: ${{error.message}}`);
  return data;
}}
'''


def _lib_r2() -> str:
    return '''\
import { S3Client, PutObjectCommand, DeleteObjectCommand, GetObjectCommand } from "@aws-sdk/client-s3";
import { getSignedUrl } from "@aws-sdk/s3-request-presigner";

const r2 = new S3Client({
  region: "auto",
  endpoint: `https://${process.env.R2_ACCOUNT_ID}.r2.cloudflarestorage.com`,
  credentials: {
    accessKeyId:     process.env.R2_ACCESS_KEY_ID!,
    secretAccessKey: process.env.R2_SECRET_ACCESS_KEY!,
  },
});

const BUCKET     = process.env.R2_BUCKET_NAME!;
const PUBLIC_URL = process.env.R2_PUBLIC_URL!;

export const uploadFile = async (key: string, body: Buffer, contentType: string) => {
  await r2.send(new PutObjectCommand({ Bucket: BUCKET, Key: key, Body: body, ContentType: contentType }));
  return `${PUBLIC_URL}/${key}`;
};

export const deleteFile = (key: string) =>
  r2.send(new DeleteObjectCommand({ Bucket: BUCKET, Key: key }));

export const presignUpload = (key: string, contentType: string, expiresIn = 3600) =>
  getSignedUrl(r2, new PutObjectCommand({ Bucket: BUCKET, Key: key, ContentType: contentType }), { expiresIn });

export const presignDownload = (key: string, expiresIn = 3600) =>
  getSignedUrl(r2, new GetObjectCommand({ Bucket: BUCKET, Key: key }), { expiresIn });
'''


def _lib_posthog() -> str:
    return '''\
import { PostHog } from "posthog-node";

export const posthogServer = new PostHog(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
  host: process.env.NEXT_PUBLIC_POSTHOG_HOST,
  flushAt: 1,
  flushInterval: 0,
});

export async function captureEvent(
  distinctId: string,
  event: string,
  properties?: Record<string, unknown>
) {
  posthogServer.capture({ distinctId, event, properties });
  await posthogServer.shutdown();
}
'''


def _sign_in_page() -> str:
    return '''\
import { SignIn } from "@clerk/nextjs";

export default function SignInPage() {
  return <SignIn />;
}
'''


def _sign_up_page() -> str:
    return '''\
import { SignUp } from "@clerk/nextjs";

export default function SignUpPage() {
  return <SignUp />;
}
'''


def _auth_layout() -> str:
    return '''\
export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen items-center justify-center">
      {children}
    </div>
  );
}
'''


def _instrumentation() -> str:
    return '''\
import * as Sentry from "@sentry/nextjs";

export async function register() {
  if (process.env.NEXT_RUNTIME === "nodejs") {
    Sentry.init({
      dsn: process.env.SENTRY_DSN,
      tracesSampleRate: 1.0,
    });
  }
  if (process.env.NEXT_RUNTIME === "edge") {
    Sentry.init({
      dsn: process.env.SENTRY_DSN,
      tracesSampleRate: 1.0,
    });
  }
}

export const onRequestError = Sentry.captureRequestError;
'''


def _dashboard_page() -> str:
    return '''\
import { auth, currentUser } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";

export default async function DashboardPage() {
  const { userId } = await auth();
  if (!userId) redirect("/sign-in");

  const user = await currentUser();

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <h1 className="text-4xl font-bold">Dashboard</h1>
      <p className="mt-4 text-gray-500">
        Welcome back{user?.firstName ? `, ${user.firstName}` : ""}!
      </p>
    </main>
  );
}
'''


def _postcss_config() -> str:
    return '''\
export default {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};
'''


def _health_route() -> str:
    return '''\
import { NextResponse } from "next/server";

/**
 * @swagger
 * /api/health:
 *   get:
 *     summary: Health check
 *     description: Returns the health status of the API.
 *     responses:
 *       200:
 *         description: API is healthy
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 status:
 *                   type: string
 *                   example: ok
 */
export async function GET() {
  return NextResponse.json({ status: "ok" }, { status: 200 });
}
'''


def _eslint_config() -> str:
    return '''\
import { dirname } from "path";
import { fileURLToPath } from "url";
import { FlatCompat } from "@eslint/eslintrc";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({ baseDirectory: __dirname });

export default [...compat.extends("next/core-web-vitals", "next/typescript")];
'''


def _welcome_email() -> str:
    return '''\
import { Html, Head, Body, Container, Section, Text, Button, Hr } from "@react-email/components";

interface WelcomeEmailProps {
  name?: string;
  actionUrl?: string;
}

export default function WelcomeEmail({ name = "there", actionUrl = "/" }: WelcomeEmailProps) {
  return (
    <Html>
      <Head />
      <Body style={{ fontFamily: "sans-serif", background: "#f6f9fc" }}>
        <Container style={{ maxWidth: 600, margin: "0 auto", padding: "40px 20px" }}>
          <Section style={{ background: "#fff", borderRadius: 8, padding: 32 }}>
            <Text style={{ fontSize: 24, fontWeight: "bold" }}>Welcome, {name}!</Text>
            <Text style={{ color: "#666", lineHeight: 1.6 }}>
              Thanks for signing up. You can get started by clicking the button below.
            </Text>
            <Button
              href={actionUrl}
              style={{ background: "#000", color: "#fff", padding: "12px 24px", borderRadius: 6, textDecoration: "none", display: "inline-block", marginTop: 16 }}
            >
              Get Started
            </Button>
            <Hr style={{ margin: "32px 0", borderColor: "#eee" }} />
            <Text style={{ color: "#999", fontSize: 12 }}>
              If you didn&apos;t create this account, you can safely ignore this email.
            </Text>
          </Section>
        </Container>
      </Body>
    </Html>
  );
}
'''


def _swagger_config(title: str) -> str:
    return f'''\
import {{ createSwaggerSpec }} from "next-swagger-doc";

export function getApiDocs() {{
  return createSwaggerSpec({{
    apiFolder: "src/app/api",
    definition: {{
      openapi: "3.0.0",
      info: {{
        title: "{title} API",
        version: "0.1.0",
      }},
    }},
  }});
}}
'''


def _api_doc_page() -> str:
    return '''\
"use client";

import SwaggerUI from "swagger-ui-react";
import "swagger-ui-react/swagger-ui.css";
import { useEffect, useState } from "react";

export default function ApiDocsPage() {
  const [spec, setSpec] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    fetch("/api/docs")
      .then((res) => res.json())
      .then(setSpec);
  }, []);

  if (!spec) return <p>Loading...</p>;
  return <SwaggerUI spec={spec} />;
}
'''


def _openapi_route() -> str:
    return '''\
import { NextResponse } from "next/server";
import { getApiDocs } from "@/lib/swagger";

export async function GET() {
  const spec = getApiDocs();
  return NextResponse.json(spec);
}
'''


def _makefile_nextjs() -> str:
    return """\
.PHONY: dev build lint test db db-stop deploy setup

dev:
\tnpm run dev

build:
\tnpm run build

lint:
\tnpm run lint && npx tsc --noEmit

test:
\tnpm test

db:
\tdocker compose up -d

db-stop:
\tdocker compose down

deploy:
\tvercel --prod

setup:
\tnpm install
"""
