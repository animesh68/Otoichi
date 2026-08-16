import React, { createContext, useContext, useState, useRef, useEffect } from 'react';

const AudioContext = createContext(null);

export function AudioProvider({ children }) {
  const [currentTrack, setCurrentTrack] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [duration, setDuration] = useState(30);
  const audioRef = useRef(new Audio());

  useEffect(() => {
    const audio = audioRef.current;

    const handleTimeUpdate = () => {
      if (audio.duration) {
        setProgress((audio.currentTime / audio.duration) * 100);
      }
    };

    const handleEnded = () => {
      setIsPlaying(false);
      setProgress(0);
    };

    const handlePlay = () => setIsPlaying(true);
    const handlePause = () => setIsPlaying(false);

    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('ended', handleEnded);
    audio.addEventListener('play', handlePlay);
    audio.addEventListener('pause', handlePause);

    return () => {
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('ended', handleEnded);
      audio.removeEventListener('play', handlePlay);
      audio.removeEventListener('pause', handlePause);
      audio.pause();
    };
  }, []);

  const playTrack = (track, albumOrArtist = {}) => {
    const audio = audioRef.current;
    
    // Use track preview, or fallback to any valid preview in the album
    let previewUrl = track.itunes_preview_url || track.preview_url;
    if (!previewUrl && albumOrArtist?.tracks && Array.isArray(albumOrArtist.tracks)) {
      const fallback = albumOrArtist.tracks.find(t => t.itunes_preview_url || t.preview_url);
      if (fallback) {
        previewUrl = fallback.itunes_preview_url || fallback.preview_url;
      }
    }

    if (!previewUrl) {
      console.warn(`No 30-second audio preview available for "${track.title}"`);
      return;
    }

    if (currentTrack?.id === track.id) {
      if (isPlaying) {
        audio.pause();
      } else {
        audio.play().catch(console.error);
      }
      return;
    }

    audio.pause();
    audio.src = previewUrl;
    audio.currentTime = 0;
    
    setCurrentTrack({
      ...track,
      cover_art_url: albumOrArtist.cover_art_url || track.cover_art_url || albumOrArtist.coverArt,
      artist_name: albumOrArtist.artist_name || track.artist_name || albumOrArtist.artistName || 'Unknown Artist',
      album_title: albumOrArtist.title || track.album_title || 'Vinyl Pressing'
    });

    audio.play().then(() => {
      setIsPlaying(true);
    }).catch(err => {
      console.warn('Audio autoplay prevented:', err);
      setIsPlaying(false);
    });
  };

  const togglePlay = () => {
    const audio = audioRef.current;
    if (isPlaying) {
      audio.pause();
    } else if (audio.src) {
      audio.play().catch(console.error);
    }
  };

  const stop = () => {
    const audio = audioRef.current;
    audio.pause();
    audio.currentTime = 0;
    setIsPlaying(false);
    setCurrentTrack(null);
  };

  return (
    <AudioContext.Provider value={{
      currentTrack,
      isPlaying,
      progress,
      duration,
      playTrack,
      togglePlay,
      stop
    }}>
      {children}
    </AudioContext.Provider>
  );
}

export const useAudio = () => useContext(AudioContext);
