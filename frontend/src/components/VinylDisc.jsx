import React from 'react';

export default function VinylDisc({ size = 180, isSpinning = false, labelColor = 'var(--brass)' }) {
  return (
    <div style={{
      width: `${size}px`,
      height: `${size}px`,
      borderRadius: '50%',
      background: 'radial-gradient(circle, #2a2622 0%, #151311 30%, #0d0c0a 70%, #050404 100%)',
      boxShadow: 'inset 0 0 10px rgba(0,0,0,0.9), 2px 4px 15px rgba(0,0,0,0.8)',
      position: 'relative',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      animation: isSpinning ? 'spinSlow 12s linear infinite' : 'none'
    }}>
      {/* Vinyl Grooves (Micro rings) */}
      <div style={{
        position: 'absolute',
        width: '88%',
        height: '88%',
        borderRadius: '50%',
        border: '1px solid rgba(243, 236, 221, 0.04)',
        boxShadow: 'inset 0 0 4px rgba(255,255,255,0.03)'
      }} />
      <div style={{
        position: 'absolute',
        width: '74%',
        height: '74%',
        borderRadius: '50%',
        border: '1px solid rgba(243, 236, 221, 0.05)'
      }} />
      <div style={{
        position: 'absolute',
        width: '60%',
        height: '60%',
        borderRadius: '50%',
        border: '1px solid rgba(243, 236, 221, 0.04)'
      }} />
      <div style={{
        position: 'absolute',
        width: '46%',
        height: '46%',
        borderRadius: '50%',
        border: '1px solid rgba(243, 236, 221, 0.06)'
      }} />

      {/* Center Label */}
      <div style={{
        width: '32%',
        height: '32%',
        borderRadius: '50%',
        background: `radial-gradient(circle, ${labelColor} 0%, #7d5c19 100%)`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        boxShadow: '0 0 8px rgba(0,0,0,0.6)',
        border: '1px solid rgba(0,0,0,0.5)'
      }}>
        {/* Spindle Hole */}
        <div style={{
          width: '24%',
          height: '24%',
          borderRadius: '50%',
          backgroundColor: '#0a0807',
          boxShadow: 'inset 0 0 3px rgba(0,0,0,0.9)'
        }} />
      </div>
    </div>
  );
}
