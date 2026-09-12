import { useState } from "react";
import { cn } from "./ui.jsx";
import Logo from "./logo.jsx";

function NavItem({ item, activeId, onSelect, level = 0 }) {
  const isActive = activeId === item.id;
  const hasChildren = Boolean(item.children?.length);
  const [open, setOpen] = useState(false);

  const handleClick = () => {
    if (hasChildren) {
      setOpen((v) => !v);
    } else {
      onSelect(item.id);
    }
  };

  return (
    <div className="flex w-full flex-col">
      <button
        type="button"
        onClick={handleClick}
        style={{ paddingLeft: `${level * 12 + 10}px` }}
        className={cn(
          "group flex items-center justify-between rounded-md py-[7px] pr-2.5 text-left transition",
          isActive
            ? "bg-white/10 font-medium text-white"
            : "text-neutral-500 hover:bg-white/5 hover:text-neutral-200"
        )}
      >
        <span className="truncate text-[13px] tracking-wide">
          {item.title}
        </span>
        <span className="flex items-center gap-2">
          {item.shortcut && (
            <kbd className="hidden h-5 items-center rounded border border-white/10 bg-white/5 px-1.5 font-mono text-[10px] text-neutral-500 group-hover:inline-flex">
              {item.shortcut}
            </kbd>
          )}
          {item.badge != null && (
            <span className="inline-flex h-5 min-w-[20px] items-center justify-center rounded-full bg-white/10 px-1.5 text-[10px] font-medium text-neutral-200">
              {item.badge}
            </span>
          )}
          {hasChildren && (
            <span
              className={cn(
                "text-xs text-neutral-500 transition-transform duration-200",
                open && "rotate-90"
              )}
            >
              ›
            </span>
          )}
        </span>
      </button>

      {hasChildren && (
        <div
          className={cn(
            "grid transition-[grid-template-rows,opacity] duration-300 ease-in-out",
            open ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"
          )}
        >
          <div className="relative flex min-h-0 flex-col gap-0.5 overflow-hidden">
            <div
              className="absolute bottom-0 top-0 border-l border-white/10"
              style={{ left: `${level * 12 + 17}px` }}
            />
            {item.children.map((child) => (
              <NavItem
                key={child.id}
                item={child}
                activeId={activeId}
                onSelect={onSelect}
                level={level + 1}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function DashboardSidebar({
  navGroups,
  bottomItems,
  activeId,
  onSelect,
  className,
}) {
  return (
    <div
      className={cn(
        "flex h-full w-[260px] shrink-0 flex-col border-r border-white/10 bg-ink-900/60 p-3",
        className
      )}
    >
      <Logo className="mb-2 px-2 py-1.5" />

      <div className="mt-2 flex flex-1 flex-col gap-4 overflow-y-auto">
        {navGroups.map((group, idx) => (
          <div key={group.heading ?? idx} className="flex flex-col gap-0.5">
            {group.heading && (
              <span className="mb-1 px-2.5 text-[11px] font-semibold uppercase tracking-wider text-neutral-600">
                {group.heading}
              </span>
            )}
            {group.items.map((item) => (
              <NavItem
                key={item.id}
                item={item}
                activeId={activeId}
                onSelect={onSelect}
              />
            ))}
          </div>
        ))}
      </div>

      <div className="mt-auto flex flex-col gap-0.5 border-t border-white/10 pt-4">
        {bottomItems.map((item) => (
          <NavItem
            key={item.id}
            item={item}
            activeId={activeId}
            onSelect={onSelect}
          />
        ))}
      </div>
    </div>
  );
}
