import React, { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

interface TechnicalDetailsProps {
  title?: string;
  children: React.ReactNode;
  className?: string;
}

export const TechnicalDetails: React.FC<TechnicalDetailsProps> = ({
  title = 'Technical details',
  children,
  className = '',
}) => {
  const [open, setOpen] = useState(false);

  return (
    <div className={`rounded-xl border border-[#E5E5E0] bg-[#FFFFFF] ${className}`}>
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className="w-full flex items-center justify-between gap-3 px-4 py-3 text-left cursor-pointer"
        aria-expanded={open}
      >
        <span className="text-xs font-heading font-bold uppercase tracking-wider text-[#525866]">
          {title}
        </span>
        {open ? (
          <ChevronUp className="w-4 h-4 text-[#525866] shrink-0" />
        ) : (
          <ChevronDown className="w-4 h-4 text-[#525866] shrink-0" />
        )}
      </button>
      {open && (
        <div className="px-4 pb-4 text-xs text-[#525866] leading-relaxed space-y-2 border-t border-[#E5E5E0] pt-3">
          {children}
        </div>
      )}
    </div>
  );
};
