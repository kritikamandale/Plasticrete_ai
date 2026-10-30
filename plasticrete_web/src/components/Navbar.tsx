import React, { useState } from 'react';
import { useMix, type MainNavRoute } from '../context/MixContext';
import { Menu, X } from 'lucide-react';

export const Navbar: React.FC = () => {
  const { mainRoute, setMainRoute } = useMix();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  type NavItem = {
    id: MainNavRoute;
    label: string;
  };

  const navLinks: NavItem[] = [
    { id: 'home', label: 'Home' },
    { id: 'studio', label: 'Mix workspace' },
    { id: 'interactive', label: 'Mix simulator' },
    { id: 'batch', label: 'Cast & Record' },
    { id: 'standards', label: 'Requirements' },
  ];

  const handleNavClick = (id: MainNavRoute) => {
    setMainRoute(id);
    setMobileMenuOpen(false);
  };

  return (
    <header className="sticky top-0 z-50 w-full bg-[#F5F5F3] border-b border-[#E5E5E0]">
      <div className="max-w-7xl mx-auto flex h-[72px] items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Left: Brand Wordmark */}
        <button
          onClick={() => {
            setMainRoute('home');
            setMobileMenuOpen(false);
          }}
          className="flex items-center gap-2.5 text-left cursor-pointer group focus:outline-none focus-visible:ring-2 focus-visible:ring-[#2563EB]"
        >
          {/* Subtle architectural geometric aggregate mark */}
          <div className="w-5 h-5 flex items-center justify-center border border-[#333A42] bg-[#333A42] text-white shrink-0">
            <span className="block w-2 h-2 bg-[#2563EB]" />
          </div>

          <div className="flex items-baseline">
            <span className="font-heading font-bold text-lg tracking-tight text-[#1E2022]">
              PlastiCrete
            </span>
            <span className="font-heading font-bold text-lg text-[#2563EB]">
              .ai
            </span>
          </div>
        </button>

        {/* Center: Clean Typographic Text Links */}
        <nav className="hidden md:flex items-center gap-3 lg:gap-6 h-full text-[13px] lg:text-sm">
          {navLinks.map((item) => {
            const isActive = mainRoute === item.id;
            return (
              <button
                key={item.id}
                onClick={() => handleNavClick(item.id)}
                className={`relative h-full flex items-center text-sm font-medium transition-colors cursor-pointer focus:outline-none focus-visible:text-[#1E2022] ${
                  isActive
                    ? 'text-[#1E2022] font-semibold'
                    : 'text-[#525866] hover:text-[#1E2022]'
                }`}
              >
                <span className="whitespace-nowrap">{item.label}</span>
                {isActive && (
                  <span className="absolute bottom-0 left-0 right-0 h-[2px] bg-[#2563EB]" />
                )}
              </button>
            );
          })}
        </nav>

        {/* Right: Engineered Primary Action */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              setMainRoute('studio');
              setMobileMenuOpen(false);
            }}
            className="hidden sm:inline-flex items-center justify-center px-4 py-2 bg-[#2563EB] hover:bg-[#1D4ED8] text-white text-xs font-medium rounded-[4px] border border-[#1D4ED8] transition-colors cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-[#2563EB]"
          >
            Open mix workspace
          </button>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 text-[#333A42] hover:text-[#1E2022] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#2563EB]"
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-[#E5E5E0] bg-[#F5F5F3] px-6 py-5 space-y-4">
          <div className="flex flex-col space-y-3">
            {navLinks.map((item) => {
              const isActive = mainRoute === item.id;
              return (
                <button
                  key={`m-${item.id}`}
                  onClick={() => handleNavClick(item.id)}
                  className={`text-left text-sm py-1.5 transition-colors ${
                    isActive
                      ? 'text-[#2563EB] font-semibold'
                      : 'text-[#525866] hover:text-[#1E2022]'
                  }`}
                >
                  {item.label}
                </button>
              );
            })}
          </div>

          <div className="pt-3 border-t border-[#E5E5E0]">
            <button
              onClick={() => {
                setMainRoute('studio');
                setMobileMenuOpen(false);
              }}
              className="w-full py-2.5 bg-[#2563EB] hover:bg-[#1D4ED8] text-white text-xs font-medium rounded-[4px] border border-[#1D4ED8] transition-colors text-center"
            >
              Open mix workspace
            </button>
          </div>
        </div>
      )}
    </header>
  );
};
