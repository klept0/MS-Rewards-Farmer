# Camoufox Integration for MS-Rewards-Farmer

## Overview

This branch integrates [Camoufox](https://github.com/daijro/camoufox), a stealth Firefox browser, into MS-Rewards-Farmer as an alternative to Chrome. Camoufox provides better anti-detection capabilities and fingerprint evasion for web scraping.

## Features

- **Anti-Detection**: Camoufox is designed to be undetectable by most anti-bot systems
- **Fingerprint Rotation**: Automatic rotation of device characteristics, OS, hardware info, etc.
- **Stealth Features**: 
  - Human-like mouse movement
  - Blocks ads and circumvents detection
  - No CSS animations for faster performance
  - WebRTC IP spoofing
  - Font and WebGL spoofing
- **Memory Efficient**: Uses less memory than standard browsers (~200MB)
- **Up-to-date**: Stays current with latest Firefox versions

## Installation

### 1. Install Dependencies

```bash
# Install Camoufox with GeoIP support
pip install 'camoufox[geoip]'

# Install other required packages
pip install -r requirements.txt
```

### 2. Download Camoufox Browser

```bash
# Download the Camoufox browser binary
python3 -m camoufox fetch
```

## Usage

### Configuration File Method

Create or modify your `config.yaml` file:

```yaml
browser:
  type: "camoufox"      # Options: "chrome", "camoufox" 
  visible: true         # Set to false for headless mode
  geolocation: "US"     # Your target location
  language: "en-US"     # Your target language
  proxy: null           # Optional proxy configuration

accounts:
  - email: "your_email@example.com"
    password: "your_password"
    totp: "your_totp_secret"  # Optional 2FA

search:
  type: "both"          # Options: "desktop", "mobile", "both"
```

### Command Line Method

```bash
# Use Camoufox for this run
python main.py --browser camoufox --visible

# Use with other options
python main.py --browser camoufox --config your_config.yaml --searchtype desktop
```

## Configuration Options

### Browser Settings

- `browser.type`: Set to `"camoufox"` to use Camoufox instead of Chrome
- `browser.visible`: Set to `true` to see the browser window, `false` for headless
- `browser.proxy`: Proxy configuration (format: `http://user:pass@host:port`)
- `browser.geolocation`: Target country code for geolocation spoofing
- `browser.language`: Target language for interface and headers

### Camoufox-Specific Features

Camoufox automatically provides:
- **Fingerprint Rotation**: Random device characteristics
- **Geolocation Matching**: Matches your IP location if using proxies
- **Human-like Behavior**: Natural mouse movements and timing
- **Ad Blocking**: Built-in uBlock Origin with privacy filters
- **Anti-Detection**: Stealth patches to avoid detection

## Comparison: Chrome vs Camoufox

| Feature | Chrome (undetected-chromedriver) | Camoufox |
|---------|----------------------------------|----------|
| Detection Evasion | Moderate | Excellent |
| Fingerprint Rotation | Limited | Advanced |
| Memory Usage | ~300-500MB | ~200MB |
| Setup Complexity | Simple | Simple |
| Update Frequency | Manual | Automatic |
| Anti-Bot Performance | Good | Excellent |
| Proxy Support | Basic | Advanced with GeoIP |

## Testing

Test your Camoufox integration:

```bash
# Run the integration test
python test_camoufox_simple.py
```

## Troubleshooting

### Common Issues

1. **"No module named camoufox"**
   ```bash
   pip install 'camoufox[geoip]'
   ```

2. **"Camoufox binary not found"**
   ```bash
   python3 -m camoufox fetch
   ```

3. **Proxy Issues**
   - Ensure proxy format is correct: `http://user:pass@host:port`
   - Test proxy connectivity outside the script first

4. **Performance Issues**
   - Set `browser.visible: false` for better performance
   - Ensure you have enough RAM (minimum 4GB recommended)

### Debug Mode

Run with debug logging to see detailed information:

```bash
python main.py --browser camoufox --debug --visible
```

## Advanced Configuration

### Custom Camoufox Options

The integration automatically configures optimal settings, but you can modify the Camoufox options in `src/camoufox_browser.py` if needed.

### Profile Management

Camoufox uses the same session directory structure as Chrome, so your existing profiles will be preserved when switching between browsers.

## Performance Tips

1. **Use Headless Mode**: Set `browser.visible: false` in production
2. **Enable Proxy GeoIP**: Use proxies with GeoIP matching for better results
3. **Monitor Memory**: Camoufox uses less memory but monitor usage with multiple accounts
4. **Update Regularly**: Keep Camoufox updated with `python3 -m camoufox fetch`

## Security Considerations

- Camoufox provides better security and privacy than standard browsers
- Built-in ad blocking and tracking protection
- Automatic fingerprint rotation reduces tracking
- WebRTC IP spoofing protects real IP when using proxies

## Contributing

When contributing to the Camoufox integration:

1. Test both Chrome and Camoufox modes
2. Ensure backward compatibility with existing configs
3. Follow the existing code patterns in `src/camoufox_browser.py`
4. Update documentation for any new features

## Support

- [Camoufox Documentation](https://camoufox.com/)
- [Camoufox GitHub](https://github.com/daijro/camoufox)
- [MS-Rewards-Farmer Issues](https://github.com/klept0/MS-Rewards-Farmer/issues)