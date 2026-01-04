/// Protocol Detail Screen
///
/// View protocol content with offline support and usage tracking.

import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class ProtocolDetailScreen extends StatefulWidget {
  final String protocolId;

  const ProtocolDetailScreen({Key? key, required this.protocolId}) : super(key: key);

  @override
  _ProtocolDetailScreenState createState() => _ProtocolDetailScreenState();
}

class _ProtocolDetailScreenState extends State<ProtocolDetailScreen>
    with SingleTickerProviderStateMixin {
  Map<String, dynamic>? protocol;
  bool isLoading = true;
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    fetchProtocol();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> fetchProtocol() async {
    setState(() => isLoading = true);

    try {
      final response = await http.get(
        Uri.parse('https://api.dora.app/api/v1/protocols/${widget.protocolId}'),
        headers: {
          'Authorization': 'Bearer ${await getAccessToken()}',
        },
      );

      if (response.statusCode == 200) {
        setState(() {
          protocol = json.decode(response.body);
          isLoading = false;
        });
      } else {
        setState(() => isLoading = false);
        _showError('Failed to load protocol');
      }
    } catch (e) {
      setState(() => isLoading = false);
      _showError('Error: $e');
    }
  }

  Future<String> getAccessToken() async {
    return 'your_access_token';
  }

  Future<void> recordUsage(bool followed) async {
    try {
      await http.post(
        Uri.parse('https://api.dora.app/api/v1/protocols/${widget.protocolId}/use'),
        headers: {
          'Authorization': 'Bearer ${await getAccessToken()}',
          'Content-Type': 'application/json',
        },
        body: json.encode({'followed': followed}),
      );

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Usage recorded successfully')),
      );

      fetchProtocol(); // Refresh to update usage count
    } catch (e) {
      _showError('Failed to record usage');
    }
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: Colors.red),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (isLoading) {
      return Scaffold(
        appBar: AppBar(title: Text('Loading...')),
        body: Center(child: CircularProgressIndicator()),
      );
    }

    if (protocol == null) {
      return Scaffold(
        appBar: AppBar(title: Text('Error')),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.error_outline, size: 64, color: Colors.red),
              SizedBox(height: 16),
              Text('Protocol not found or access denied'),
              ElevatedButton(
                onPressed: () => Navigator.pop(context),
                child: Text('Go Back'),
              ),
            ],
          ),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: Text(protocol!['title'] ?? 'Protocol'),
        actions: [
          IconButton(
            icon: Icon(Icons.download),
            onPressed: () {
              // Implement offline download
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text('Downloaded for offline use')),
              );
            },
            tooltip: 'Download for Offline',
          ),
          IconButton(
            icon: Icon(Icons.share),
            onPressed: () {
              // Implement sharing
            },
            tooltip: 'Share',
          ),
        ],
      ),
      body: Column(
        children: [
          // Protocol Header
          Container(
            padding: EdgeInsets.all(16),
            color: Colors.blue[50],
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        protocol!['title'] ?? '',
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                    _buildStatusChip(protocol!['status']),
                  ],
                ),
                SizedBox(height: 8),
                Text(
                  protocol!['description'] ?? '',
                  style: TextStyle(color: Colors.grey[700]),
                ),
                SizedBox(height: 12),
                Row(
                  children: [
                    Icon(Icons.analytics, size: 16, color: Colors.grey),
                    SizedBox(width: 4),
                    Text(
                      '${protocol!['usage_count'] ?? 0} uses',
                      style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                    ),
                    SizedBox(width: 16),
                    Icon(Icons.history, size: 16, color: Colors.grey),
                    SizedBox(width: 4),
                    Text(
                      'Version ${protocol!['version_number'] ?? '1.0'}',
                      style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                    ),
                  ],
                ),
              ],
            ),
          ),

          // Tabs
          TabBar(
            controller: _tabController,
            labelColor: Theme.of(context).primaryColor,
            tabs: [
              Tab(text: 'Content'),
              Tab(text: 'Versions'),
              Tab(text: 'Comments'),
            ],
          ),

          // Tab Views
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: [
                // Content Tab
                SingleChildScrollView(
                  padding: EdgeInsets.all(16),
                  child: Markdown(
                    data: protocol!['content'] ?? 'No content available',
                    shrinkWrap: true,
                    physics: NeverScrollableScrollPhysics(),
                  ),
                ),

                // Versions Tab
                Center(child: Text('Version history will be shown here')),

                // Comments Tab
                Center(child: Text('Team comments will be shown here')),
              ],
            ),
          ),

          // Action Bar
          Container(
            padding: EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.white,
              boxShadow: [
                BoxShadow(
                  color: Colors.grey.withOpacity(0.2),
                  spreadRadius: 1,
                  blurRadius: 4,
                ),
              ],
            ),
            child: Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: () => recordUsage(true),
                    icon: Icon(Icons.check_circle),
                    label: Text('Used Protocol'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.green,
                      padding: EdgeInsets.symmetric(vertical: 12),
                    ),
                  ),
                ),
                SizedBox(width: 12),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () => recordUsage(false),
                    icon: Icon(Icons.report_problem),
                    label: Text('Deviation'),
                    style: OutlinedButton.styleFrom(
                      padding: EdgeInsets.symmetric(vertical: 12),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatusChip(String? status) {
    Color color;
    switch (status) {
      case 'published':
        color = Colors.green;
        break;
      case 'review':
        color = Colors.orange;
        break;
      default:
        color = Colors.grey;
    }

    return Container(
      padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.2),
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text(
        (status ?? 'draft').toUpperCase(),
        style: TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.bold,
          color: color,
        ),
      ),
    );
  }
}
