import React from 'react';

export default function HankoStamp({ text = "音市", size = 28, rotation = -3 }) {
  return (
    <div style={{
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      width: `${size}px`,
      height: `${size}px`,
      borderRadius: '50%',
      border: '1.5px solid var(--seal)',
      color: 'var(--seal)',
      fontFamily: 'var(--font-script)',
      fontSize: `${size * 0.46}px`,
      lineHeight: '1',
      transform: `rotate(${rotation}deg)`,
      boxShadow: '0 0 6px var(--seal-glow)',
      userSelect: 'none',
      letterSpacing: '-0.05em'
    }}>
      {text}
    </div>
  );
}
