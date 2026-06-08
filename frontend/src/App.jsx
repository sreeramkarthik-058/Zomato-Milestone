import React, { useState } from 'react';
import { 
  MapPin, 
  Star, 
  Sparkles, 
  Heart, 
  Clock, 
  Calendar, 
  Search, 
  RefreshCw, 
  AlertTriangle 
} from 'lucide-react';

function App() {
  // Navigation & View State
  const [view, setView] = useState('search'); // 'search' | 'loading' | 'results'
  
  // Form Input States
  const [location, setLocation] = useState('Bangalore');
  const [selectedCuisines, setSelectedCuisines] = useState(['Japanese']);
  const [budgetBand, setBudgetBand] = useState('$'); // '$' | '$$' | '$$$' | '$$$$'
  const [rating, setRating] = useState(4); // 1 to 5 stars
  const [additionalPrefs, setAdditionalPrefs] = useState('');
  
  // API Call States
  const [recommendations, setRecommendations] = useState([]);
  const [summary, setSummary] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  // Favorites state (ids of favorited restaurants)
  const [favorites, setFavorites] = useState({});

  const cuisinesList = ['Italian', 'Japanese', 'French', 'Mexican', 'Contemporary'];

  // Toggle cuisine chip selection
  const handleCuisineToggle = (cuisine) => {
    if (selectedCuisines.includes(cuisine)) {
      setSelectedCuisines(selectedCuisines.filter(c => c !== cuisine));
    } else {
      // For backend we usually require a single primary search cuisine, 
      // but we let them select multiple on frontend and we join them or pick the first.
      setSelectedCuisines([...selectedCuisines, cuisine]);
    }
  };

  // Map budget segment to API low/medium/high
  const getApiBudget = (segment) => {
    switch (segment) {
      case '$': return 'low';
      case '$$': return 'medium';
      case '$$$':
      case '$$$$':
        return 'high';
      default: return 'medium';
    }
  };

  // AI enhance text prompt helper
  const handleAIEnhance = () => {
    const defaultEnhancements = [
      "Romantic spot with quiet ambient music and scenic window seating.",
      "Lively atmosphere suitable for a group dinner with great acoustics.",
      "Hidden gem with artisanal cocktail pairings and highly attentive service.",
      "Cozy family-friendly vibe with quick service and authentic flavor profiles."
    ];
    // Pick a random one or append
    const randomEnhancement = defaultEnhancements[Math.floor(Math.random() * defaultEnhancements.length)];
    setAdditionalPrefs(prev => prev ? `${prev} ${randomEnhancement}` : randomEnhancement);
  };

  // Submit preferences to Python backend FastAPI
  const handleFindTable = async (e) => {
    if (e) e.preventDefault();
    
    if (!location.trim()) {
      setErrorMsg('Please specify a dining location.');
      return;
    }

    if (selectedCuisines.length === 0) {
      setErrorMsg('Please select at least one preferred cuisine.');
      return;
    }

    setErrorMsg('');
    setView('loading');

    // Build preferences payload matching UserPreferences pydantic model
    const payload = {
      location: location.trim(),
      budget: getApiBudget(budgetBand),
      cuisine: selectedCuisines[0], // pass primary selected cuisine
      min_rating: parseFloat(rating),
      additional_preferences: additionalPrefs.trim() ? additionalPrefs.trim() : null
    };

    try {
      const response = await fetch('http://localhost:8000/api/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error(`Server returned status code: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.status === 'success') {
        setRecommendations(data.recommendations);
        setSummary(data.summary || '');
        setView('results');
      } else if (data.status === 'no_matches') {
        setRecommendations([]);
        setSummary('');
        setView('no_matches');
      } else {
        // Error status from orchestrator
        setErrorMsg(data.message || 'An error occurred while fetching recommendations.');
        setView('search');
      }
    } catch (err) {
      console.error(err);
      setErrorMsg(`Failed to connect to the backend server. Make sure FastAPI is running on port 8000.`);
      setView('search');
    }
  };

  // Toggle favorite restaurant
  const toggleFavorite = (id) => {
    setFavorites(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  // Back to search screen
  const handleBackToSearch = () => {
    setView('search');
    setErrorMsg('');
  };

  return (
    <div>
      {/* Navigation Header */}
      <header className="app-header">
        <a href="#" className="brand-logo" onClick={handleBackToSearch}>
          Chef AI
        </a>
        <nav className="nav-links">
          <a 
            href="#" 
            className={`nav-link ${view === 'search' || view === 'loading' ? 'active' : ''}`}
            onClick={handleBackToSearch}
          >
            Search
          </a>
          <a href="#" className="nav-link">About</a>
          <a href="#" className="nav-link">Contact</a>
        </nav>
        <div className="header-right">
          <div className="header-location">
            <MapPin size={16} />
            <span>New York, NY</span>
          </div>
          <div className="header-search-icon">
            <Search size={18} />
          </div>
        </div>
      </header>

      {/* Main Body content */}
      <main className="main-content">
        
        {/* Error alert */}
        {errorMsg && (
          <div style={{
            backgroundColor: '#fee2e2',
            border: '1px solid #fca5a5',
            borderRadius: '8px',
            padding: '16px',
            maxWidth: '680px',
            margin: '20px auto',
            color: '#991b1b',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            fontSize: '14px',
            fontWeight: '600'
          }}>
            <AlertTriangle size={18} />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* 1. Search Form View */}
        {view === 'search' && (
          <div className="form-card">
            <h1 className="form-title">Find Your Perfect Table</h1>
            <p className="form-subtitle">
              Tell us your preferences and let our AI concierge curate the ideal dining experience.
            </p>

            <form onSubmit={handleFindTable}>
              {/* Location Input */}
              <div className="form-group">
                <span className="label-medium">Where are you dining?</span>
                <div className="input-with-icon">
                  <span className="input-icon-prefix">
                    <MapPin size={18} />
                  </span>
                  <input 
                    type="text" 
                    className="input-field"
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    placeholder="Neighborhood, city, or zip code" 
                    required
                  />
                </div>
              </div>

              {/* Cuisine chips */}
              <div className="form-group">
                <span className="label-medium">Preferred Cuisines</span>
                <div className="chips-container">
                  {cuisinesList.map(c => (
                    <button
                      type="button"
                      key={c}
                      className={`chip ${selectedCuisines.includes(c) ? 'active' : ''}`}
                      onClick={() => handleCuisineToggle(c)}
                    >
                      {c}
                    </button>
                  ))}
                  <button type="button" className="chip more-chip">+ More</button>
                </div>
              </div>

              {/* Grid: Budget Band & Minimum Rating */}
              <div className="form-grid-2">
                
                {/* Budget Band segments */}
                <div className="form-group">
                  <span className="label-medium">Budget Band</span>
                  <div className="budget-segmented">
                    {['$', '$$', '$$$', '$$$$'].map(seg => (
                      <button
                        type="button"
                        key={seg}
                        className={`budget-segment ${budgetBand === seg ? 'active' : ''}`}
                        onClick={() => setBudgetBand(seg)}
                      >
                        {seg}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Stars Selection */}
                <div className="form-group">
                  <span className="label-medium">Minimum Rating</span>
                  <div className="stars-container">
                    {[1, 2, 3, 4, 5].map(starNum => (
                      <button
                        type="button"
                        key={starNum}
                        className={`star-btn ${starNum <= rating ? 'filled' : ''}`}
                        onClick={() => setRating(starNum)}
                      >
                        <Star size={24} fill={starNum <= rating ? '#d4af37' : 'none'} strokeWidth={2} />
                      </button>
                    ))}
                  </div>
                </div>

              </div>

              {/* Additional preferences textarea */}
              <div className="form-group">
                <span className="label-medium">Additional Preferences</span>
                <div className="textarea-container">
                  <textarea
                    className="textarea-field"
                    value={additionalPrefs}
                    onChange={(e) => setAdditionalPrefs(e.target.value)}
                    placeholder="Describe the mood: 'Romantic anniversary spot with a view' or 'Lively place for a group of 8 with good acoustics'..."
                  />
                  <button 
                    type="button" 
                    className="ai-enhance-btn"
                    onClick={handleAIEnhance}
                  >
                    <Sparkles size={13} style={{ color: '#d31027' }} />
                    <span>AI Enhanced</span>
                  </button>
                </div>
              </div>

              {/* Large Action Button */}
              <button type="submit" className="submit-btn">
                Find My Table
              </button>

            </form>
          </div>
        )}

        {/* 2. Loading State View */}
        {view === 'loading' && (
          <div className="loader-container">
            <div className="spinner"></div>
            <h3 style={{ fontWeight: 600, fontSize: '18px', color: '#1a1c1e', marginBottom: '8px' }}>
              Curating your dining experience
            </h3>
            <p style={{ color: '#74777f', fontSize: '14px' }}>
              Our AI concierge is matching your preferences with our dataset...
            </p>
          </div>
        )}

        {/* 3. No Matches View */}
        {view === 'no_matches' && (
          <div className="no-matches-container">
            <h2 className="no-matches-title">🍱 No matching restaurants found</h2>
            <p className="no-matches-text">
              We couldn't find any restaurants in <strong>{location}</strong> matching <strong>{selectedCuisines[0]}</strong> with rating ≥ {rating} within budget band {budgetBand}.
            </p>
            <button 
              type="button" 
              className="submit-btn" 
              style={{ maxWidth: '200px', margin: '0 auto', display: 'block' }}
              onClick={handleBackToSearch}
            >
              Adjust Preferences
            </button>
          </div>
        )}

        {/* 4. Results Page View */}
        {view === 'results' && (
          <div>
            {/* Header info */}
            <div className="results-header-section">
              <h1 className="results-title">Top Matches</h1>
              <p className="results-subtitle">
                {summary ? summary : `AI curated selection based on your preference for "${location} • ${selectedCuisines[0]} cuisine".`}
              </p>
            </div>

            {/* Grid Layout */}
            <div className="results-layout">
              
              {/* Left Column: List of Restaurant Cards */}
              <div className="left-cards-column">
                {recommendations.slice(0, 3).map((rec, index) => {
                  const isFav = !!favorites[rec.restaurant_id || index];
                  return (
                    <div className="match-card" key={rec.restaurant_id || index}>
                      
                      <div className="card-header-row">
                        <div className="match-tag">
                          {index === 0 ? 'Top Match' : 'Highly Recommended'}
                          <span className="match-tag-span">• {rec.cuisine}</span>
                        </div>
                        <button 
                          className="fav-btn"
                          onClick={() => toggleFavorite(rec.restaurant_id || index)}
                        >
                          <Heart 
                            size={20} 
                            fill={isFav ? '#d31027' : 'none'} 
                            stroke={isFav ? '#d31027' : 'currentColor'} 
                          />
                        </button>
                      </div>

                      <h2 className="restaurant-title">{rec.restaurant_name}</h2>

                      <div className="rating-cost-row">
                        <span className="star-rating-gold">★ {rec.rating.toFixed(1)}</span>
                        <span style={{ color: '#74777f' }}>•</span>
                        <span>{rec.estimated_cost}</span>
                      </div>

                      {/* AI Rationale box */}
                      <div className="card-ai-rationale">
                        <div className="rationale-title">
                          <Sparkles size={11} />
                          <span>AI Rationale</span>
                        </div>
                        <p className="rationale-text">
                          {rec.explanation}
                        </p>
                      </div>

                      {/* Card Bottom bar */}
                      <div className="card-bottom-row">
                        <div className="meta-details">
                          <div className="meta-item">
                            <Clock size={14} />
                            <span>12 min walk</span>
                          </div>
                          <div className="meta-item">
                            <Calendar size={14} />
                            <span>Tables available</span>
                          </div>
                        </div>
                        <button className="options-btn">
                          View Table Options
                        </button>
                      </div>

                    </div>
                  );
                })}
              </div>

              {/* Right Column: Refine AI & Secondary Cards */}
              <div className="right-sidebar-column">
                
                {/* Refine card */}
                <div className="right-sidebar-card">
                  <h3 className="sidebar-title">Refine AI Selection</h3>
                  <div className="sidebar-subtitle">Texture Profile</div>
                  <div className="chips-container" style={{ marginBottom: '16px' }}>
                    <button className="chip active" style={{ padding: '6px 14px', fontSize: '12px' }}>Umami</button>
                    <button className="chip" style={{ padding: '6px 14px', fontSize: '12px' }}>Crispy</button>
                    <button className="chip" style={{ padding: '6px 14px', fontSize: '12px' }}>Velvety</button>
                  </div>
                  <button className="refine-btn" onClick={handleBackToSearch}>
                    Update Rationale
                  </button>
                </div>

                {/* Secondary Recommendations (from index 3 onwards) */}
                {recommendations.slice(3, 5).map((rec, index) => (
                  <div className="right-sidebar-card" key={rec.restaurant_id || index + 3}>
                    <div className="mini-title-row">
                      <h4 className="mini-name">{rec.restaurant_name}</h4>
                      <span className="mini-rating" style={{ color: '#d4af37' }}>☆ {rec.rating.toFixed(1)}</span>
                    </div>
                    <div className="mini-subtitle">{rec.cuisine} • {rec.estimated_cost.split(' ')[0] || '$$'}</div>
                    <div className="mini-quote-box">
                      "{rec.explanation.split('.')[0]}."
                    </div>
                    <button className="check-avail-btn">
                      Check Availability
                    </button>
                  </div>
                ))}

                {/* Fallback Static item if fewer than 5 recommendations */}
                {recommendations.length < 4 && (
                  <div className="right-sidebar-card">
                    <div className="mini-title-row">
                      <h4 className="mini-name">Ether Dining</h4>
                      <span className="mini-rating" style={{ color: '#d4af37' }}>☆ 4.7</span>
                    </div>
                    <div className="mini-subtitle">Nordic Fusion • $$$</div>
                    <div className="mini-quote-box">
                      "Matches your preference for minimalist plating and high-contrast flavor profiles."
                    </div>
                    <button className="check-avail-btn">
                      Check Availability
                    </button>
                  </div>
                )}

              </div>

            </div>
          </div>
        )}

      </main>

      {/* Footer component */}
      <footer className="app-footer">
        <div className="footer-left">
          <strong>Chef AI</strong>
          <span>&copy; 2024 Epicurean Pulse. AI-Powered Gastronomy.</span>
        </div>
        <div className="footer-right">
          <a href="#" className="footer-link">About Us</a>
          <a href="#" className="footer-link">Partner with Us</a>
          <a href="#" className="footer-link">Privacy Policy</a>
          <a href="#" className="footer-link">Terms of Service</a>
          <a href="#" className="footer-link">Contact</a>
        </div>
      </footer>
    </div>
  );
}

export default App;
