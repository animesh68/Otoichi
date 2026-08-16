// Helper to extract unified display properties from ProductResponse or AlbumResponse
export function getProductDisplay(item) {
  if (!item) return {
    id: '',
    title: 'Vinyl Record',
    artistName: 'Various Artists',
    coverArt: '',
    price: 29.99,
    format: '12" LP',
    sleeveCondition: 'NM',
    mediaCondition: 'M',
    genre: 'Rock',
    releaseYear: 2022,
    sku: 'OT-LP-01'
  };

  // If item is CartItemResponse, the product is in item.product
  const p = item.product || item;
  const album = p.album || (p.tracks ? p : null);
  const track = p.track || null;

  const title = album?.title || track?.title || p.title || 'Vinyl Record';
  const artistName = album?.artist?.name || p.artist_name || (typeof p.artist === 'string' ? p.artist : 'Various Artists');
  const coverArt = album?.cover_art_url || p.cover_art_url || (p.image_urls && p.image_urls[0]) || '';
  const price = typeof p.price === 'number' ? p.price : (Number(p.price) || 29.99);
  const format = p.format || (p.product_type === 'single' ? '7" Single' : '12" LP');
  const sleeveCondition = p.sleeve_condition || 'NM';
  const mediaCondition = p.media_condition || 'M';
  const genre = album?.genre || p.genre || 'Rock';
  const releaseYear = album?.release_year || p.release_year || 2022;
  const sku = p.sku || 'OT-VINYL';

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
    rawProduct: p,
    rawAlbum: album
  };
}
