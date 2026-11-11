import { useEffect, useState, useTransition } from "react";

export function usePathname(): string {
  const [pathname, setPathname] = useState<string>(() => {
    if (typeof window === "undefined") return "/";
    return window.location.pathname || "/";
  });

  useEffect(() => {
    const handleLocationChange = () => {
      setPathname(window.location.pathname || "/");
    };

    window.addEventListener("popstate", handleLocationChange);
    return () => {
      window.removeEventListener("popstate", handleLocationChange);
    };
  }, []);

  return pathname;
}

export function useRouter() {
  const [, startTransition] = useTransition();

  return {
    push(url: string) {
      window.history.pushState({}, "", url);
      window.dispatchEvent(new PopStateEvent("popstate"));
    },
    replace(url: string) {
      window.history.replaceState({}, "", url);
      window.dispatchEvent(new PopStateEvent("popstate"));
    },
    refresh() {
      startTransition(() => {
        window.dispatchEvent(new PopStateEvent("popstate"));
      });
    },
    back() {
      window.history.back();
    },
    forward() {
      window.history.forward();
    },
  };
}

export function useSearchParams(): URLSearchParams {
  const [searchParams, setSearchParams] = useState<URLSearchParams>(() => {
    if (typeof window === "undefined") return new URLSearchParams();
    return new URLSearchParams(window.location.search);
  });

  useEffect(() => {
    const handleLocationChange = () => {
      setSearchParams(new URLSearchParams(window.location.search));
    };

    window.addEventListener("popstate", handleLocationChange);
    return () => {
      window.removeEventListener("popstate", handleLocationChange);
    };
  }, []);

  return searchParams;
}
