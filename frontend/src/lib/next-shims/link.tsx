import React, { forwardRef } from "react";

export interface LinkProps extends React.AnchorHTMLAttributes<HTMLAnchorElement> {
  href: string;
  replace?: boolean;
  scroll?: boolean;
  prefetch?: boolean;
  asChild?: boolean;
}

export const Link = forwardRef<HTMLAnchorElement, LinkProps>(
  ({ href, onClick, replace, children, ...props }, ref) => {
    const handleClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
      if (onClick) onClick(e);
      if (
        !e.defaultPrevented &&
        e.button === 0 &&
        (!props.target || props.target === "_self") &&
        !e.metaKey &&
        !e.ctrlKey &&
        !e.altKey &&
        !e.shiftKey &&
        href.startsWith("/")
      ) {
        e.preventDefault();
        if (replace) {
          window.history.replaceState({}, "", href);
        } else {
          window.history.pushState({}, "", href);
        }
        window.dispatchEvent(new PopStateEvent("popstate"));
      }
    };

    return (
      <a ref={ref} href={href} onClick={handleClick} {...props}>
        {children}
      </a>
    );
  }
);

Link.displayName = "Link";
export default Link;
