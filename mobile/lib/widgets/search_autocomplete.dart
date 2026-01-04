import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../theme.dart';
import '../providers/search_provider.dart';

class SearchAutocomplete extends ConsumerStatefulWidget {
  final TextEditingController controller;
  final Function(String) onSubmit;
  final String hintText;
  final bool showVoiceButton;

  const SearchAutocomplete({
    super.key,
    required this.controller,
    required this.onSubmit,
    this.hintText = 'Ask a medical question...',
    this.showVoiceButton = true,
  });

  @override
  ConsumerState<SearchAutocomplete> createState() => _SearchAutocompleteState();
}

class _SearchAutocompleteState extends ConsumerState<SearchAutocomplete> {
  final FocusNode _focusNode = FocusNode();
  final LayerLink _layerLink = LayerLink();
  OverlayEntry? _overlayEntry;
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _focusNode.addListener(_onFocusChange);
    widget.controller.addListener(_onTextChange);
  }

  @override
  void dispose() {
    _focusNode.removeListener(_onFocusChange);
    widget.controller.removeListener(_onTextChange);
    _focusNode.dispose();
    _hideOverlay();
    super.dispose();
  }

  void _onFocusChange() {
    if (_focusNode.hasFocus && widget.controller.text.length >= 2) {
      _showOverlay();
    } else if (!_focusNode.hasFocus) {
      Future.delayed(const Duration(milliseconds: 200), _hideOverlay);
    }
  }

  void _onTextChange() {
    final text = widget.controller.text;
    if (text.length >= 2) {
      _fetchSuggestions(text);
      _showOverlay();
    } else {
      _hideOverlay();
    }
  }

  Future<void> _fetchSuggestions(String query) async {
    setState(() => _isLoading = true);
    await ref.read(searchSuggestionsProvider(query).future);
    setState(() => _isLoading = false);
    _updateOverlay();
  }

  void _showOverlay() {
    if (_overlayEntry != null) return;

    _overlayEntry = _createOverlayEntry();
    Overlay.of(context).insert(_overlayEntry!);
  }

  void _hideOverlay() {
    _overlayEntry?.remove();
    _overlayEntry = null;
  }

  void _updateOverlay() {
    _overlayEntry?.markNeedsBuild();
  }

  OverlayEntry _createOverlayEntry() {
    final renderBox = context.findRenderObject() as RenderBox;
    final size = renderBox.size;

    return OverlayEntry(
      builder: (context) => Positioned(
        width: size.width,
        child: CompositedTransformFollower(
          link: _layerLink,
          showWhenUnlinked: false,
          offset: Offset(0, size.height + 4),
          child: Material(
            elevation: 8,
            borderRadius: BorderRadius.circular(12),
            child: _buildSuggestionsList(),
          ),
        ),
      ),
    );
  }

  Widget _buildSuggestionsList() {
    final query = widget.controller.text;
    final suggestions = ref.watch(searchSuggestionsProvider(query));

    return Container(
      constraints: const BoxConstraints(maxHeight: 300),
      decoration: BoxDecoration(
        color: DoraColors.bgPrimary,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: DoraColors.borderColor),
      ),
      child: suggestions.when(
        data: (data) {
          if (data.isEmpty) {
            return _buildEmptySuggestions();
          }
          return ListView.builder(
            shrinkWrap: true,
            padding: EdgeInsets.zero,
            itemCount: data.length,
            itemBuilder: (context, index) => _buildSuggestionItem(data[index]),
          );
        },
        loading: () => Padding(
          padding: const EdgeInsets.all(16),
          child: Center(
            child: SizedBox(
              width: 20,
              height: 20,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                color: DoraColors.primary,
              ),
            ),
          ),
        ),
        error: (_, __) => _buildEmptySuggestions(),
      ),
    );
  }

  Widget _buildEmptySuggestions() {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        _buildQuickActions(),
        const Divider(height: 1),
        _buildRecentSearches(),
      ],
    );
  }

  Widget _buildQuickActions() {
    return Padding(
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Quick Actions',
            style: TextStyle(
              color: DoraColors.textSecondary,
              fontSize: 12,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              _buildQuickActionChip('Drug interaction', Icons.warning),
              _buildQuickActionChip('Calculate GFR', Icons.calculate),
              _buildQuickActionChip('Dosing', Icons.medication),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildQuickActionChip(String label, IconData icon) {
    return InkWell(
      onTap: () {
        widget.controller.text = label;
        _hideOverlay();
        widget.onSubmit(label);
      },
      borderRadius: BorderRadius.circular(16),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        decoration: BoxDecoration(
          color: DoraColors.primary.withOpacity(0.1),
          borderRadius: BorderRadius.circular(16),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 14, color: DoraColors.primary),
            const SizedBox(width: 4),
            Text(
              label,
              style: TextStyle(
                color: DoraColors.primary,
                fontSize: 12,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRecentSearches() {
    final recents = ref.watch(recentSearchesProvider);

    return recents.when(
      data: (data) {
        if (data.isEmpty) return const SizedBox.shrink();

        return Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'Recent Searches',
                    style: TextStyle(
                      color: DoraColors.textSecondary,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  GestureDetector(
                    onTap: () => ref.read(recentSearchesProvider.notifier).clear(),
                    child: Text(
                      'Clear',
                      style: TextStyle(
                        color: DoraColors.primary,
                        fontSize: 12,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              ...data.take(5).map((search) => _buildRecentItem(search)),
            ],
          ),
        );
      },
      loading: () => const SizedBox.shrink(),
      error: (_, __) => const SizedBox.shrink(),
    );
  }

  Widget _buildRecentItem(String search) {
    return InkWell(
      onTap: () {
        widget.controller.text = search;
        _hideOverlay();
        widget.onSubmit(search);
      },
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 8),
        child: Row(
          children: [
            Icon(
              Icons.history,
              size: 16,
              color: DoraColors.textSecondary,
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                search,
                style: const TextStyle(fontSize: 14),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ),
            Icon(
              Icons.north_west,
              size: 14,
              color: DoraColors.textSecondary,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSuggestionItem(Map<String, dynamic> suggestion) {
    final type = suggestion['type'] ?? 'query';
    IconData icon;
    Color iconColor;

    switch (type) {
      case 'drug':
        icon = Icons.medication;
        iconColor = Colors.green;
        break;
      case 'calculator':
        icon = Icons.calculate;
        iconColor = Colors.blue;
        break;
      case 'condition':
        icon = Icons.medical_information;
        iconColor = Colors.orange;
        break;
      default:
        icon = Icons.search;
        iconColor = DoraColors.textSecondary;
    }

    return InkWell(
      onTap: () {
        widget.controller.text = suggestion['text'] ?? '';
        _hideOverlay();
        widget.onSubmit(suggestion['text'] ?? '');
      },
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Row(
          children: [
            Icon(icon, size: 20, color: iconColor),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    suggestion['text'] ?? '',
                    style: const TextStyle(fontSize: 14),
                  ),
                  if (suggestion['subtitle'] != null)
                    Text(
                      suggestion['subtitle'],
                      style: TextStyle(
                        fontSize: 12,
                        color: DoraColors.textSecondary,
                      ),
                    ),
                ],
              ),
            ),
            if (type != 'query')
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: iconColor.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  type.toUpperCase(),
                  style: TextStyle(
                    fontSize: 10,
                    color: iconColor,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return CompositedTransformTarget(
      link: _layerLink,
      child: Container(
        decoration: BoxDecoration(
          color: DoraColors.bgSecondary,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: DoraColors.borderColor),
        ),
        child: Row(
          children: [
            const SizedBox(width: 16),
            Icon(Icons.search, color: DoraColors.textSecondary),
            const SizedBox(width: 12),
            Expanded(
              child: TextField(
                controller: widget.controller,
                focusNode: _focusNode,
                decoration: InputDecoration(
                  hintText: widget.hintText,
                  border: InputBorder.none,
                  hintStyle: TextStyle(color: DoraColors.textSecondary),
                ),
                onSubmitted: (value) {
                  _hideOverlay();
                  widget.onSubmit(value);
                },
              ),
            ),
            if (_isLoading)
              Padding(
                padding: const EdgeInsets.all(12),
                child: SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: DoraColors.primary,
                  ),
                ),
              ),
            if (widget.showVoiceButton && !_isLoading)
              IconButton(
                icon: Icon(Icons.mic, color: DoraColors.primary),
                onPressed: _startVoiceInput,
              ),
          ],
        ),
      ),
    );
  }

  void _startVoiceInput() {
    // TODO: Implement voice input
  }
}
