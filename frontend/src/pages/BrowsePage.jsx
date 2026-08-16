import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { SlidersHorizontal, ArrowUpDown, Disc, Search } from 'lucide-react';
import ProductCard from '../components/ProductCard';
import FilterDrawer from '../components/FilterDrawer';
import { CatalogService } from '../api/services';

const QUICK_TABS = [
  { label: 'ALL', value: '' },
  { label: 'VINYL LP', value: 'album' },
  { label: '7" SINGLES', value: 'single' },
  { label: 'ROCK', value: 'Rock' },
  { label: 'ALTERNATIVE', value: 'Alternative Rock' },
  { label: 'HIP-HOP & R&B', value: 'Hip-Hop' },
  { label: 'POP & SOUL', value: 'Pop' }
];

export default function BrowsePage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [totalCount, setTotalCount] = useState(0);

  // Filters state
  const [searchTerm, setSearchTerm] = useState(searchParams.get('search') || '');
  const [selectedGenre, setSelectedGenre] = useState(searchParams.get('genre') || '');
  const [selectedFormat, setSelectedFormat] = useState(searchParams.get('format') || '');
  const [selectedCondition, setSelectedCondition] = useState(searchParams.get('condition') || '');
  const [productType, setProductType] = useState(searchParams.get('type') || '');
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');
  const [isFilterDrawerOpen, setIsFilterDrawerOpen] = useState(false);

  // Active quick tab
  const [activeTab, setActiveTab] = useState(searchParams.get('genre') || searchParams.get('type') || '');

  useEffect(() => {
    async function fetchCatalog() {
      try {
        setLoading(true);
        const params = {
          limit: 100,
          search: searchTerm || undefined,
          genre: selectedGenre || undefined,
          format: selectedFormat || undefined,
          condition: selectedCondition || undefined,
          product_type: productType || undefined,
          sort_by: sortBy,
          sort_order: sortOrder
        };

        const res = await CatalogService.getProducts(params);
        const items = res?.items || res || [];
        setProducts(items);
        setTotalCount(res?.total || items.length);
      } catch (err) {
        console.error('Failed to load browse products:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchCatalog();
  }, [searchTerm, selectedGenre, selectedFormat, selectedCondition, productType, sortBy, sortOrder]);

  const handleTabClick = (tab) => {
    setActiveTab(tab.value);
    if (tab.value === 'album' || tab.value === 'single') {
      setProductType(tab.value);
      setSelectedGenre('');
    } else if (tab.value === '') {
      setProductType('');
      setSelectedGenre('');
    } else {
      setSelectedGenre(tab.value);
      setProductType('');
    }
  };

  const handleSortChange = (e) => {
    const val = e.target.value;
    if (val === 'newest') {
      setSortBy('created_at');
      setSortOrder('desc');
    } else if (val === 'price_asc') {
      setSortBy('price');
      setSortOrder('asc');
    } else if (val === 'price_desc') {
      setSortBy('price');
      setSortOrder('desc');
    } else if (val === 'title_asc') {
      setSortBy('title');
      setSortOrder('asc');
    }
  };

  const handleResetFilters = () => {
    setSelectedGenre('');
    setSelectedFormat('');
    setSelectedCondition('');
    setProductType('');
    setSearchTerm('');
    setActiveTab('');
    setIsFilterDrawerOpen(false);
  };

  return (
    <div style={{ backgroundColor: 'var(--bg)', minHeight: '100vh', paddingBottom: '100px' }}>
      
      {/* Category Quick Pills Header (Inspired by reference frame) */}
      <div style={{
        backgroundColor: '#0D0B0A',
        borderBottom: '1px solid var(--taupe-border)',
        padding: '16px 0'
      }}>
        <div className="container" style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          overflowX: 'auto',
          paddingBottom: '4px'
        }}>
          {QUICK_TABS.map((tab) => {
            const isActive = activeTab === tab.value;
            return (
              <button
                key={tab.label}
                onClick={() => handleTabClick(tab)}
                style={{
                  padding: '7px 18px',
                  borderRadius: 'var(--radius-full)',
                  fontSize: '0.8rem',
                  fontFamily: 'var(--font-mono)',
                  letterSpacing: '0.04em',
                  whiteSpace: 'nowrap',
                  backgroundColor: isActive ? 'var(--brass)' : 'transparent',
                  color: isActive ? '#100E0C' : 'var(--ink-secondary)',
                  border: isActive ? '1px solid var(--brass)' : '1px solid rgba(243, 236, 221, 0.15)',
                  fontWeight: isActive ? 600 : 400,
                  transition: 'var(--transition-smooth)'
                }}
              >
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Sticky Toolbar under Nav */}
      <div style={{
        position: 'sticky',
        top: 0,
        zIndex: 50,
        backgroundColor: 'rgba(16, 14, 12, 0.95)',
        backdropFilter: 'blur(10px)',
        borderBottom: '1px solid var(--taupe-border)',
        padding: '14px 0'
      }}>
        <div className="container" style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '16px'
        }}>
          {/* Left: Item Count */}
          <div style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '0.88rem',
            color: 'var(--ink-secondary)',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <Disc size={16} color="var(--brass)" />
            <span>{loading ? 'Searching...' : `${totalCount} records listed`}</span>
          </div>

          {/* Center Search Bar */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            backgroundColor: 'var(--taupe)',
            border: '1px solid var(--taupe-border)',
            borderRadius: 'var(--radius-full)',
            padding: '6px 14px',
            width: '280px'
          }}>
            <Search size={15} color="var(--text-muted)" style={{ marginRight: '8px' }} />
            <input
              type="text"
              placeholder="Search artist, album, track..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--ink)',
                fontSize: '0.84rem',
                width: '100%'
              }}
            />
          </div>

          {/* Right: Sort & Filter Controls */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {/* Sort Dropdown */}
            <div style={{ position: 'relative' }}>
              <select
                onChange={handleSortChange}
                defaultValue="newest"
                style={{
                  appearance: 'none',
                  backgroundColor: 'var(--taupe)',
                  border: '1px solid var(--taupe-border)',
                  color: 'var(--ink)',
                  padding: '7px 32px 7px 14px',
                  borderRadius: 'var(--radius-full)',
                  fontSize: '0.82rem',
                  fontFamily: 'var(--font-body)',
                  cursor: 'pointer'
                }}
              >
                <option value="newest">Newest Arrivals</option>
                <option value="price_asc">Price: Low to High</option>
                <option value="price_desc">Price: High to Low</option>
                <option value="title_asc">Title: A to Z</option>
              </select>
              <ArrowUpDown size={13} color="var(--text-muted)" style={{ position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none' }} />
            </div>

            {/* Filter Toggle Button */}
            <button
              onClick={() => setIsFilterDrawerOpen(true)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                backgroundColor: (selectedGenre || selectedFormat || selectedCondition) ? 'rgba(200, 155, 60, 0.2)' : 'var(--taupe)',
                border: (selectedGenre || selectedFormat || selectedCondition) ? '1px solid var(--brass)' : '1px solid var(--taupe-border)',
                color: (selectedGenre || selectedFormat || selectedCondition) ? 'var(--brass)' : 'var(--ink)',
                padding: '7px 16px',
                borderRadius: 'var(--radius-full)',
                fontSize: '0.82rem',
                fontFamily: 'var(--font-body)',
                fontWeight: 500
              }}
            >
              <SlidersHorizontal size={14} />
              <span>Filters</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Catalog Grid */}
      <div className="container" style={{ marginTop: '36px' }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '100px 0', color: 'var(--text-muted)' }}>
            <Disc size={36} color="var(--brass)" style={{ animation: 'spinSlow 2s linear infinite', marginBottom: '16px' }} />
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.9rem' }}>Digging crates from live catalog...</p>
          </div>
        ) : products.length === 0 ? (
          <div style={{
            textAlign: 'center',
            padding: '80px 24px',
            backgroundColor: 'var(--bg-card)',
            border: '1px solid var(--taupe-border)',
            borderRadius: 'var(--radius-lg)',
            maxWidth: '520px',
            margin: '40px auto'
          }}>
            <Disc size={40} color="var(--brass)" style={{ marginBottom: '16px' }} />
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.4rem', color: 'var(--ink)', marginBottom: '8px' }}>
              No Records Found
            </h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '24px' }}>
              We couldn't find any pressings matching your current filter criteria.
            </p>
            <button onClick={handleResetFilters} className="btn-brass">
              Clear All Filters
            </button>
          </div>
        ) : (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
            gap: '28px'
          }}>
            {products.map((prod) => (
              <ProductCard key={prod.id} product={prod} />
            ))}
          </div>
        )}
      </div>

      {/* Filter Drawer Component */}
      <FilterDrawer
        isOpen={isFilterDrawerOpen}
        onClose={() => setIsFilterDrawerOpen(false)}
        selectedGenre={selectedGenre}
        setSelectedGenre={setSelectedGenre}
        selectedFormat={selectedFormat}
        setSelectedFormat={setSelectedFormat}
        selectedCondition={selectedCondition}
        setSelectedCondition={setSelectedCondition}
        onReset={handleResetFilters}
      />
    </div>
  );
}
