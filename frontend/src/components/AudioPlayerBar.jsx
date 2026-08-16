import React from 'react';
import { Play, Pause, X, ExternalLink } from 'lucide-react';
import { useAudio } from '../context/AudioContext';

export default function AudioPlayerBar() {
  const { currentTrack, isPlaying, progress, togglePlay, stop } = useAudio();

  if (!currentTrack) return null;

  return (
    <div style={{
      position: 'fixed',
      bottom: '24px',
      left: '50%',
      transform: 'translateX(-50%)',
      width: 'calc(100% - 48px)',
      maxWidth: '780px',
      backgroundColor: '#1C1814',
      border: '1px solid var(--brass)',
      borderRadius: 'var(--radius-lg)',
      padding: '12px 20px',
      boxShadow: '0 12px 40px rgba(0, 0, 0, 0.8), 0 0 20px var(--brass-glow)',
      zIndex: 900,
      display: 'flex',
      alignItems: 'center',
      gap: '16px',
      backdropFilter: 'blur(10px)',
      animation: 'fadeIn 0.3s ease-out'
    }}>
      {/* Track Art Thumbnail */}
      <div style={{
        width: '46px',
        height: '46px',
        borderRadius: 'var(--radius-sm)',
        overflow: 'hidden',
        flexShrink: 0,
        backgroundColor: '#000'
      }}>
        {currentTrack.cover_art_url ? (
          <img
            src={currentTrack.cover_art_url}
            alt={currentTrack.title}
            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
          />
        ) : (
          <div style={{ width: '100%', height: '100%', backgroundColor: 'var(--taupe)' }} />
        )}
      </div>

      {/* Track Info */}
      <div style={{ flexGrow: 1, minWidth: 0 }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          marginBottom: '4px'
        }}>
          <span style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '0.68rem',
            color: 'var(--brass)',
            textTransform: 'uppercase'
          }}>
            30s Master Sample
          </span>
        </div>
        <div style={{
          fontFamily: 'var(--font-body)',
          fontWeight: 600,
          fontSize: '0.92rem',
          color: 'var(--ink)',
          whiteSpace: 'nowrap',
          overflow: 'hidden',
          textOverflow: 'ellipsis'
        }}>
          {currentTrack.title}
        </div>
        <div style={{
          fontSize: '0.78rem',
          color: 'var(--text-muted)',
          whiteSpace: 'nowrap',
          overflow: 'hidden',
          textOverflow: 'ellipsis'
        }}>
          {currentTrack.artist_name} {currentTrack.album_title ? `• ${currentTrack.album_title}` : ''}
        </div>

        {/* Playback Progress Bar */}
        <div style={{
          width: '100%',
          height: '3px',
          backgroundColor: 'rgba(243, 236, 221, 0.15)',
          borderRadius: 'var(--radius-full)',
          marginTop: '6px',
          overflow: 'hidden'
        }}>
          <div style={{
            height: '100%',
            width: `${progress}%`,
            backgroundColor: 'var(--brass)',
            transition: 'width 0.15s linear'
          }} />
        </div>
      </div>

      {/* Controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <button
          onClick={togglePlay}
          aria-label={isPlaying ? "Pause" : "Play"}
          style={{
            width: '40px',
            height: '40px',
            borderRadius: '50%',
            backgroundColor: 'var(--brass)',
            color: '#100E0C',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'var(--transition-smooth)'
          }}
        >
          {isPlaying ? <Pause size={18} fill="#100E0C" /> : <Play size={18} fill="#100E0C" style={{ marginLeft: '2px' }} />}
        </button>

        {currentTrack.spotify_track_id && (
          <a
            href={`https://open.spotify.com/track/${currentTrack.spotify_track_id}`}
            target="_blank"
            rel="noopener noreferrer"
            title="Open on Spotify"
            style={{
              color: 'var(--text-muted)',
              display: 'flex',
              alignItems: 'center',
              padding: '6px'
            }}
          >
            <ExternalLink size={18} />
          </a>
        )}

        <button
          onClick={stop}
          aria-label="Close audio player"
          style={{
            color: 'var(--text-muted)',
            padding: '6px',
            display: 'flex',
            alignItems: 'center'
          }}
        >
          <X size={18} />
        </button>
      </div>
    </div>
  );
}
