import 'package:flutter/material.dart';
import '../theme.dart';

class QueryInput extends StatefulWidget {
  final Function(String) onSubmit;
  final bool isLoading;
  final VoidCallback? onVoice;

  const QueryInput({
    super.key,
    required this.onSubmit,
    this.isLoading = false,
    this.onVoice,
  });

  @override
  State<QueryInput> createState() => _QueryInputState();
}

class _QueryInputState extends State<QueryInput> {
  final _controller = TextEditingController();
  final _focusNode = FocusNode();

  @override
  void dispose() {
    _controller.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  void _handleSubmit() {
    final text = _controller.text.trim();
    if (text.isNotEmpty && !widget.isLoading) {
      widget.onSubmit(text);
      _controller.clear();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: DoraColors.bgPrimary,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, -5),
          ),
        ],
      ),
      child: SafeArea(
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            // Voice button
            if (widget.onVoice != null)
              IconButton(
                icon: const Icon(Icons.mic),
                color: DoraColors.primary,
                onPressed: widget.onVoice,
              ),

            // Text input
            Expanded(
              child: Container(
                constraints: const BoxConstraints(maxHeight: 120),
                child: TextField(
                  controller: _controller,
                  focusNode: _focusNode,
                  maxLines: null,
                  textInputAction: TextInputAction.send,
                  onSubmitted: (_) => _handleSubmit(),
                  decoration: InputDecoration(
                    hintText: 'Ask a medical question...',
                    hintStyle: const TextStyle(color: DoraColors.textTertiary),
                    filled: true,
                    fillColor: DoraColors.bgSecondary,
                    contentPadding: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 12,
                    ),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(24),
                      borderSide: BorderSide.none,
                    ),
                  ),
                ),
              ),
            ),
            const SizedBox(width: 8),

            // Send button
            Container(
              decoration: BoxDecoration(
                color: widget.isLoading
                    ? DoraColors.textTertiary
                    : DoraColors.primary,
                shape: BoxShape.circle,
              ),
              child: IconButton(
                icon: widget.isLoading
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          valueColor: AlwaysStoppedAnimation(Colors.white),
                        ),
                      )
                    : const Icon(Icons.send),
                color: Colors.white,
                onPressed: widget.isLoading ? null : _handleSubmit,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
