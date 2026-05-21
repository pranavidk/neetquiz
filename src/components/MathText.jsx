import React from 'react';
import { InlineMath, BlockMath } from 'react-katex';

export default function MathText({ text }) {
  if (typeof text !== 'string') {
    return text;
  }

  // Split the string on $$...$$ and $...$ delimiters.
  // Using [\s\S] matches any character including newlines.
  const parts = text.split(/(\$\$[\s\S]*?\$\$|\$[\s\S]*?\$)/g);

  return (
    <>
      {parts.map((part, index) => {
        if (part.startsWith('$$') && part.endsWith('$$')) {
          const math = part.slice(2, -2);
          return (
            <BlockMath
              key={index}
              math={math}
              renderError={(error) => {
                console.error("KaTeX block render error:", error);
                return <span>{part}</span>;
              }}
            />
          );
        } else if (part.startsWith('$') && part.endsWith('$')) {
          const math = part.slice(1, -1);
          return (
            <InlineMath
              key={index}
              math={math}
              renderError={(error) => {
                console.error("KaTeX inline render error:", error);
                return <span>{part}</span>;
              }}
            />
          );
        } else {
          return <span key={index}>{part}</span>;
        }
      })}
    </>
  );
}
