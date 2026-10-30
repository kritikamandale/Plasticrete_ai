import React from 'react';

interface FieldHelpProps {
  children: React.ReactNode;
}

export const FieldHelp: React.FC<FieldHelpProps> = ({ children }) => (
  <p className="text-[11px] text-[#525866] mt-1 leading-relaxed">{children}</p>
);
