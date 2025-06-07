import React, { useState } from 'react';
import { Home, CreditCard, Bot, Settings, Menu, X } from 'lucide-react';

const LingvoPalNavbar = () => {
  const [activeTab, setActiveTab] = useState('Dashboard');
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const navItems = [
    {
      name: 'Dashboard',
      icon: Home,
      href: '/dashboard',
      color: 'bg-blue-500',
      hoverColor: 'hover:bg-blue-50',
    },
    {
      name: 'Flashcards',
      icon: CreditCard,
      href: '/flashcards',
      color: 'bg-green-500',
      hoverColor: 'hover:bg-green-50',
    },
    {
      name: 'AI Tutor',
      icon: Bot,
      href: '/ai-tutor',
      color: 'bg-purple-500',
      hoverColor: 'hover:bg-purple-50',
    },
    {
      name: 'Settings',
      icon: Settings,
      href: '/settings',
      color: 'bg-gray-500',
      hoverColor: 'hover:bg-gray-50',
    },
  ];

  const handleNavClick = (itemName: string, href: string) => {
    setActiveTab(itemName);
    setIsMobileMenuOpen(false);
    // Optional: Programmatic navigation if using a router
    // window.location.href = href; // Uncomment if not using React Router
  };

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen((prev) => !prev);
  };

  return (
    <nav className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-20 montserrat">
          {/* Logo */}
          <div className="flex items-center">
            <a href="/" className="flex-shrink-0">
              <span className="text-4xl font-bold ">
                <span className="text-blue-600">Lingvo</span>
                <span className="text-blue-600">Pal</span>
              </span>
            </a>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex md:items-center md:space-x-4">
            {navItems.map((item) => {
              const IconComponent = item.icon;
              const isActive = activeTab === item.name;

              return (
                <a
                  key={item.name}
                  href={item.href}
                  onClick={() => handleNavClick(item.name, item.href)}
                  className={`
                    relative px-4 py-2 rounded-xl font-medium text-sm transition-all duration-200 ease-in-out
                    flex items-center space-x-2 group min-w-max
                    ${isActive
                      ? 'bg-gradient-to-r from-blue-500 to-green-500 text-white shadow-md'
                      : 'text-gray-700 hover:text-blue-600 hover:bg-blue-50'
                    }
                  `}
                  aria-current={isActive ? 'page' : undefined}
                >
                  <div
                    className={`
                      p-1 rounded-md transition-all duration-200
                      ${isActive
                        ? 'bg-white/20'
                        : 'bg-gray-100 group-hover:bg-blue-100'
                      }
                    `}
                  >
                    <IconComponent
                      className={`
                        w-4 h-4 transition-all duration-200
                        ${isActive ? 'text-white' : 'text-gray-600 group-hover:text-blue-600'}
                      `}
                      aria-hidden="true"
                    />
                  </div>
                  <span className="font-medium whitespace-nowrap">{item.name}</span>
                  {isActive && (
                    <div className="absolute -bottom-0.5 left-1/2 transform -translate-x-1/2">
                      <div className="w-1 h-1 bg-white rounded-full" />
                    </div>
                  )}
                </a>
              );
            })}
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              onClick={toggleMobileMenu}
              className="inline-flex items-center justify-center p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors duration-200"
              aria-controls="mobile-menu"
              aria-expanded={isMobileMenuOpen}
              aria-label={isMobileMenuOpen ? 'Close menu' : 'Open menu'}
            >
              {isMobileMenuOpen ? (
                <X className="h-6 w-6" aria-hidden="true" />
              ) : (
                <Menu className="h-6 w-6" aria-hidden="true" />
              )}
            </button>
          </div>
        </div>

        {/* Mobile Navigation Menu */}
        <div
          id="mobile-menu"
          className={`md:hidden transition-all duration-300 ease-in-out ${
            isMobileMenuOpen ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0 overflow-hidden'
          }`}
        >
          <div className="px-2 pt-2 pb-3 space-y-2 bg-gray-50 rounded-lg mt-2 mb-4">
            {navItems.map((item) => {
              const IconComponent = item.icon;
              const isActive = activeTab === item.name;

              return (
                <a
                  key={item.name}
                  href={item.href}
                  onClick={() => handleNavClick(item.name, item.href)}
                  className={`
                    w-full text-left px-4 py-3 rounded-xl font-medium text-sm transition-all duration-300
                    flex items-center space-x-3 group
                    ${isActive
                      ? 'bg-gradient-to-r from-blue-500 to-green-500 text-white shadow-lg'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-white'
                    }
                  `}
                  aria-current={isActive ? 'page' : undefined}
                >
                  <div
                    className={`
                      p-2 rounded-lg transition-all duration-300
                      ${isActive
                        ? 'bg-white/20'
                        : `${item.color} bg-opacity-10 group-hover:bg-opacity-20`
                      }
                    `}
                  >
                    <IconComponent
                      className={`
                        w-5 h-5 transition-all duration-300
                        ${isActive ? 'text-white' : 'text-gray-600 group-hover:text-gray-800'}
                      `}
                      aria-hidden="true"
                    />
                  </div>
                  <span className="font-semibold flex-1">{item.name}</span>
                  {isActive && (
                    <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
                  )}
                </a>
              );
            })}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default LingvoPalNavbar;