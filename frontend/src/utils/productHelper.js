// Helper to extract unified display properties from ProductResponse or AlbumResponse
export function getProductDisplay(item) {
  if (!item) return {
    id: '',
    title: 'Vinyl Record',
    artistName: 'Otoichi Select',
    coverArt: '',
    price: 29.99,
    format: '12" LP',
    sleeveCondition: 'NM',
    mediaCondition: 'M',
    genre: 'Rock',
    releaseYear: 2022,
    sku: 'OT-LP-01',
    tracks: []
  };

  // If item is CartItemResponse, the product is in item.product
  const p = item.product || item;
  const album = p.album || (p.tracks ? p : null);
  const track = p.track || (!p.album && p.title ? p : null);

  const title = track?.title || album?.title || p.title || 'Vinyl Record';
  const artistName = track?.artist_name || track?.artist?.name || album?.artist_name || album?.artist?.name || p.artist_name || (typeof p.artist === 'string' ? p.artist : 'Otoichi Select');
  const coverArt = album?.cover_art_url || p.cover_art_url || (p.image_urls && p.image_urls[0]) || '';
  const price = typeof p.price === 'number' ? p.price : (Number(p.price) || (p.product_type === 'single' ? 14.99 : 29.99));
  const format = p.format || (p.product_type === 'single' ? '7" Single' : '12" LP');
  const sleeveCondition = p.sleeve_condition || 'NM';
  const mediaCondition = p.media_condition || 'M';
  const genre = album?.genre || p.genre || 'Rock & Indie';
  const releaseYear = album?.release_year || p.release_year || 2024;
  const sku = p.sku || 'OT-VINYL';

  // Extract all playable tracks whether LP album or 7" single
  let tracks = [];
  if (album?.tracks && Array.isArray(album.tracks) && album.tracks.length > 0) {
    tracks = album.tracks;
  } else if (p.tracks && Array.isArray(p.tracks) && p.tracks.length > 0) {
    tracks = p.tracks;
  } else if (track && (track.itunes_preview_url || track.spotify_track_id || track.title)) {
    tracks = [{
      id: track.id || p.id,
      title: track.title || title,
      artist_name: artistName,
      duration_ms: track.duration_ms || 210000,
      itunes_preview_url: track.itunes_preview_url,
      spotify_track_id: track.spotify_track_id,
      track_number: 1,
      is_single: true
    }];
  }

  return {
    id: p.id || item.id,
    title,
    artistName,
    coverArt,
    price,
    format,
    sleeveCondition,
    mediaCondition,
    genre,
    releaseYear,
    sku,
    tracks,
    track,
    rawProduct: p,
    rawAlbum: album
  };
}
