# Dora Beta - Known Issues and Limitations

## Current Limitations

### Knowledge Base
- **Initial content pending**: The knowledge base needs to be populated with medical content. This is a manual curation process.
- **Coverage**: Currently optimized for general medicine; specialty-specific content may be limited.

### Voice Features
- **Wake word accuracy**: "Hey DocAssist" detection may have reduced accuracy in noisy environments.
- **Accent support**: STT is optimized for Indian English and US English. Other accents may have reduced accuracy.
- **Background noise**: Voice recognition works best in quiet environments.

### Offline Mode
- **Initial sync required**: Users must sync at least once while online before using offline features.
- **Local LLM quality**: Offline LLM (Qwen 2.5 3B) provides reduced quality compared to cloud models.
- **Sync delay**: Changes made offline may take up to 5 minutes to sync when back online.

### Performance
- **Cold start**: First query after service restart may take 5-10 seconds.
- **Large documents**: PDFs over 100 pages may experience slower processing.
- **Concurrent users**: Performance may degrade with >100 simultaneous users during beta.

### Mobile App
- **iOS**: Push notifications require additional configuration.
- **Android**: Background sync may be affected by battery optimization settings.

### Integration
- **EMR sync**: Real-time sync interval is 30 seconds minimum.
- **Academic writing**: Citation formatting limited to APA and Vancouver styles.

## Known Bugs

### High Priority
1. **None currently** - All high priority bugs addressed

### Medium Priority
1. Audio overview generation may timeout for documents >50 pages
2. Document comparison may miss changes in embedded tables
3. Annotation export to PDF may have formatting issues on some documents

### Low Priority
1. Dark mode toggle may require page refresh in some browsers
2. Keyboard shortcuts may conflict with screen readers
3. Very long drug names may truncate in mobile view

## Workarounds

### Audio Timeout
If audio overview generation times out:
1. Try generating for a shorter document section
2. Use text summary instead
3. Split large documents before uploading

### Annotation Export
If PDF export has issues:
1. Use Markdown export as alternative
2. Export to JSON and format externally

### Offline Sync
If offline changes aren't syncing:
1. Check network connectivity
2. Force sync from Settings > Sync Now
3. If persistent, clear local cache and re-sync

## Reporting Issues

Please report new issues via:
- **Email**: beta-feedback@docassist.health
- **In-app**: Settings > Report Issue
- **GitHub**: [Issues Page] (for technical issues)

Include:
- Steps to reproduce
- Expected vs actual behavior
- Device/browser information
- Screenshots if applicable

---

*Last Updated: January 2026*
*Beta Version: 0.9.0*
