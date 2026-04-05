"""Expo (React Native) mobile templates."""

import json


def generate_mobile(root, ctx: dict, write, is_nextjs: bool = True) -> None:
    name  = ctx["name"]
    title = ctx["title"]
    github_user = ctx.get("github_user", "yourusername") or "yourusername"

    print("\n📱 Generating Expo mobile app...")

    write(root, "mobile/package.json",          _package_json(name))
    write(root, "mobile/app.json",              _app_json(name, title, github_user))
    write(root, "mobile/tsconfig.json",         _tsconfig())
    write(root, "mobile/app/_layout.tsx",       _root_layout())
    write(root, "mobile/app/index.tsx",         _index())
    write(root, "mobile/app/(auth)/sign-in.tsx", _sign_in())
    write(root, "mobile/lib/api.ts",            _api_client())
    write(root, "mobile/.env.example",          _env_example(is_nextjs))


def _package_json(name: str) -> str:
    return json.dumps({
        "name": f"{name}-mobile",
        "version": "0.1.0",
        "main": "expo-router/entry",
        "scripts": {
            "start":   "expo start",
            "android": "expo start --android",
            "ios":     "expo start --ios",
        },
        "dependencies": {
            "expo":              "~52.0.0",
            "expo-router":       "~4.0.0",
            "expo-status-bar":   "~2.0.0",
            "expo-secure-store": "^14",
            "react":             "18.3.2",
            "react-native":      "0.76.6",
            "@clerk/clerk-expo": "^2",
            "posthog-react-native": "^3",
            "@sentry/react-native": "^6",
        },
        "devDependencies": {
            "typescript":    "^5",
            "@types/react":  "~18.3.12",
        },
    }, indent=2)


def _app_json(name: str, title: str, github_user: str = "yourusername") -> str:
    bundle = f"com.{github_user}.{name.replace('-', '')}"
    return json.dumps({
        "expo": {
            "name": title,
            "slug": name,
            "version": "1.0.0",
            "orientation": "portrait",
            "scheme": name,
            "userInterfaceStyle": "automatic",
            "ios": {"supportsTablet": True, "bundleIdentifier": bundle},
            "android": {
                "adaptiveIcon": {
                    "foregroundImage": "./assets/adaptive-icon.png",
                    "backgroundColor": "#ffffff",
                },
                "package": bundle,
            },
            "plugins": ["expo-router", "expo-secure-store"],
            "experiments": {"typedRoutes": True},
        }
    }, indent=2)


def _tsconfig() -> str:
    return json.dumps({
        "extends": "expo/tsconfig.base",
        "compilerOptions": {"strict": True, "paths": {"@/*": ["./*"]}},
    }, indent=2)


def _root_layout() -> str:
    return '''\
import { ClerkProvider } from "@clerk/clerk-expo";
import * as SecureStore from "expo-secure-store";
import * as Sentry from "@sentry/react-native";
import { PostHogProvider } from "posthog-react-native";
import { Slot } from "expo-router";

Sentry.init({
  dsn: process.env.EXPO_PUBLIC_SENTRY_DSN,
  tracesSampleRate: 1.0,
});

const tokenCache = {
  async getToken(key: string) { return SecureStore.getItemAsync(key); },
  async saveToken(key: string, value: string) { return SecureStore.setItemAsync(key, value); },
};

export default function RootLayout() {
  return (
    <ClerkProvider
      publishableKey={process.env.EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY!}
      tokenCache={tokenCache}
    >
      <PostHogProvider
        apiKey={process.env.EXPO_PUBLIC_POSTHOG_KEY!}
        options={{ host: process.env.EXPO_PUBLIC_POSTHOG_HOST ?? "https://us.i.posthog.com" }}
      >
        <Slot />
      </PostHogProvider>
    </ClerkProvider>
  );
}
'''


def _index() -> str:
    return '''\
import { View, Text, TouchableOpacity, StyleSheet } from "react-native";
import { Link } from "expo-router";
import { useAuth } from "@clerk/clerk-expo";

export default function HomeScreen() {
  const { isSignedIn, signOut } = useAuth();
  return (
    <View style={s.container}>
      <Text style={s.title}>Welcome</Text>
      {isSignedIn ? (
        <TouchableOpacity style={s.btn} onPress={() => signOut()}>
          <Text style={s.btnText}>Sign Out</Text>
        </TouchableOpacity>
      ) : (
        <Link href="/(auth)/sign-in" asChild>
          <TouchableOpacity style={s.btn}>
            <Text style={s.btnText}>Sign In</Text>
          </TouchableOpacity>
        </Link>
      )}
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, alignItems: "center", justifyContent: "center", padding: 24 },
  title:     { fontSize: 32, fontWeight: "bold", marginBottom: 32 },
  btn:       { backgroundColor: "#000", borderRadius: 8, paddingVertical: 14, paddingHorizontal: 32 },
  btnText:   { color: "#fff", fontWeight: "600", fontSize: 16 },
});
'''


def _sign_in() -> str:
    return '''\
import { useSignIn } from "@clerk/clerk-expo";
import { useRouter } from "expo-router";
import { useState } from "react";
import { View, Text, TextInput, TouchableOpacity, StyleSheet } from "react-native";

export default function SignInScreen() {
  const { signIn, setActive, isLoaded } = useSignIn();
  const router = useRouter();
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [error, setError]       = useState("");

  async function onSignIn() {
    if (!isLoaded) return;
    try {
      const res = await signIn.create({ identifier: email, password });
      if (res.status === "complete") {
        await setActive({ session: res.createdSessionId });
        router.replace("/");
      }
    } catch (e: any) {
      setError(e.errors?.[0]?.message ?? "Sign in failed");
    }
  }

  return (
    <View style={s.container}>
      <Text style={s.title}>Sign In</Text>
      <TextInput style={s.input} placeholder="Email"    value={email}    onChangeText={setEmail}    autoCapitalize="none" keyboardType="email-address" />
      <TextInput style={s.input} placeholder="Password" value={password} onChangeText={setPassword} secureTextEntry />
      {error ? <Text style={s.error}>{error}</Text> : null}
      <TouchableOpacity style={s.btn} onPress={onSignIn}>
        <Text style={s.btnText}>Sign In</Text>
      </TouchableOpacity>
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, justifyContent: "center", padding: 24 },
  title:     { fontSize: 28, fontWeight: "bold", marginBottom: 32 },
  input:     { borderWidth: 1, borderColor: "#ddd", borderRadius: 8, padding: 12, marginBottom: 16, fontSize: 16 },
  btn:       { backgroundColor: "#000", borderRadius: 8, padding: 16, alignItems: "center", marginTop: 8 },
  btnText:   { color: "#fff", fontWeight: "600", fontSize: 16 },
  error:     { color: "red", marginBottom: 12 },
});
'''


def _api_client() -> str:
    return (
        'import { useAuth } from "@clerk/clerk-expo";\n'
        '\n'
        'const BASE = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8787/api";\n'
        '\n'
        '/** Hook returning an authenticated API client */\n'
        'export function useApi() {\n'
        '  const { getToken } = useAuth();\n'
        '\n'
        '  async function request<T>(path: string, init: RequestInit = {}): Promise<T> {\n'
        '    const token = await getToken();\n'
        '    const res = await fetch(`${BASE}${path}`, {\n'
        '      ...init,\n'
        '      headers: {\n'
        '        "Content-Type": "application/json",\n'
        '        Authorization: `Bearer ${token}`,\n'
        '        ...init.headers,\n'
        '      },\n'
        '    });\n'
        '    if (!res.ok) throw new Error((await res.text()) || res.statusText);\n'
        '    return res.json() as Promise<T>;\n'
        '  }\n'
        '\n'
        '  return {\n'
        '    get:  <T>(path: string)                => request<T>(path),\n'
        '    post: <T>(path: string, body: unknown) => request<T>(path, { method: "POST", body: JSON.stringify(body) }),\n'
        '    put:  <T>(path: string, body: unknown) => request<T>(path, { method: "PUT",  body: JSON.stringify(body) }),\n'
        '    del:  <T>(path: string)                => request<T>(path, { method: "DELETE" }),\n'
        '  };\n'
        '}\n'
    )


def _env_example(is_nextjs: bool = True) -> str:
    port = "3000" if is_nextjs else "8787"
    return f"""\
EXPO_PUBLIC_API_URL=http://localhost:{port}/api
EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_
EXPO_PUBLIC_POSTHOG_KEY=phc_
EXPO_PUBLIC_POSTHOG_HOST=https://us.i.posthog.com
EXPO_PUBLIC_SENTRY_DSN=https://
"""
