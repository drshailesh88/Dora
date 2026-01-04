/// Protocol List Screen
///
/// Mobile interface for browsing and searching protocols.

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class ProtocolListScreen extends StatefulWidget {
  @override
  _ProtocolListScreenState createState() => _ProtocolListScreenState();
}

class _ProtocolListScreenState extends State<ProtocolListScreen> {
  List<dynamic> protocols = [];
  bool isLoading = true;
  String searchQuery = '';
  String selectedCategory = '';

  final categories = [
    'emergency',
    'chronic_care',
    'procedures',
    'medications',
    'cardiology',
    'neurology',
  ];

  @override
  void initState() {
    super.initState();
    fetchProtocols();
  }

  Future<void> fetchProtocols() async {
    setState(() => isLoading = true);

    try {
      // In production, use proper base URL and authentication
      final uri = Uri.parse('https://api.dora.app/api/v1/protocols')
          .replace(queryParameters: {
        if (searchQuery.isNotEmpty) 'search': searchQuery,
        if (selectedCategory.isNotEmpty) 'category': selectedCategory,
      });

      final response = await http.get(
        uri,
        headers: {
          'Authorization': 'Bearer ${await getAccessToken()}',
        },
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        setState(() {
          protocols = data['protocols'] ?? [];
          isLoading = false;
        });
      }
    } catch (e) {
      print('Error fetching protocols: $e');
      setState(() => isLoading = false);
    }
  }

  Future<String> getAccessToken() async {
    // Implement token retrieval from secure storage
    return 'your_access_token';
  }

  Color getCategoryColor(String category) {
    final colors = {
      'emergency': Colors.red,
      'chronic_care': Colors.blue,
      'procedures': Colors.purple,
      'medications': Colors.green,
      'cardiology': Colors.pink,
      'neurology': Colors.indigo,
    };
    return colors[category] ?? Colors.grey;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Clinical Protocols'),
        actions: [
          IconButton(
            icon: Icon(Icons.book),
            onPressed: () {
              Navigator.pushNamed(context, '/protocols/references');
            },
            tooltip: 'Quick References',
          ),
          IconButton(
            icon: Icon(Icons.checklist),
            onPressed: () {
              Navigator.pushNamed(context, '/protocols/checklists');
            },
            tooltip: 'Checklists',
          ),
        ],
      ),
      body: Column(
        children: [
          // Search and Filters
          Container(
            padding: EdgeInsets.all(16),
            color: Colors.grey[100],
            child: Column(
              children: [
                TextField(
                  decoration: InputDecoration(
                    hintText: 'Search protocols...',
                    prefixIcon: Icon(Icons.search),
                    filled: true,
                    fillColor: Colors.white,
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8),
                      borderSide: BorderSide.none,
                    ),
                  ),
                  onChanged: (value) {
                    setState(() => searchQuery = value);
                    fetchProtocols();
                  },
                ),
                SizedBox(height: 12),
                SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(
                    children: [
                      _buildCategoryChip('All', ''),
                      ...categories.map((cat) => _buildCategoryChip(
                        cat.replaceAll('_', ' ').toUpperCase(),
                        cat,
                      )),
                    ],
                  ),
                ),
              ],
            ),
          ),

          // Protocol List
          Expanded(
            child: isLoading
                ? Center(child: CircularProgressIndicator())
                : protocols.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.description, size: 64, color: Colors.grey),
                            SizedBox(height: 16),
                            Text(
                              'No protocols found',
                              style: TextStyle(fontSize: 18, color: Colors.grey),
                            ),
                          ],
                        ),
                      )
                    : RefreshIndicator(
                        onRefresh: fetchProtocols,
                        child: ListView.builder(
                          padding: EdgeInsets.all(16),
                          itemCount: protocols.length,
                          itemBuilder: (context, index) {
                            final protocol = protocols[index];
                            return _buildProtocolCard(protocol);
                          },
                        ),
                      ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          Navigator.pushNamed(context, '/protocols/create');
        },
        child: Icon(Icons.add),
        tooltip: 'Create Protocol',
      ),
    );
  }

  Widget _buildCategoryChip(String label, String value) {
    final isSelected = selectedCategory == value;
    return Padding(
      padding: EdgeInsets.only(right: 8),
      child: FilterChip(
        label: Text(label),
        selected: isSelected,
        onSelected: (selected) {
          setState(() {
            selectedCategory = selected ? value : '';
          });
          fetchProtocols();
        },
        selectedColor: Theme.of(context).primaryColor.withOpacity(0.3),
      ),
    );
  }

  Widget _buildProtocolCard(Map<String, dynamic> protocol) {
    final category = protocol['category'] ?? '';
    final tags = List<String>.from(protocol['tags'] ?? []);

    return Card(
      margin: EdgeInsets.only(bottom: 12),
      child: InkWell(
        onTap: () {
          Navigator.pushNamed(
            context,
            '/protocols/detail',
            arguments: protocol['id'],
          );
        },
        child: Padding(
          padding: EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      protocol['title'] ?? '',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  if (protocol['is_clinic_wide'] == true)
                    Chip(
                      label: Text('CLINIC-WIDE', style: TextStyle(fontSize: 10)),
                      backgroundColor: Colors.purple[100],
                      padding: EdgeInsets.all(4),
                      materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    ),
                ],
              ),
              SizedBox(height: 8),
              Text(
                protocol['description'] ?? '',
                style: TextStyle(color: Colors.grey[600]),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
              SizedBox(height: 12),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  Chip(
                    label: Text(
                      category.replaceAll('_', ' ').toUpperCase(),
                      style: TextStyle(fontSize: 12),
                    ),
                    backgroundColor: getCategoryColor(category).withOpacity(0.2),
                    padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                  ),
                  ...tags.take(2).map((tag) => Chip(
                        label: Text('#$tag', style: TextStyle(fontSize: 12)),
                        backgroundColor: Colors.grey[200],
                        padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                      )),
                ],
              ),
              SizedBox(height: 8),
              Row(
                children: [
                  Icon(Icons.bar_chart, size: 16, color: Colors.grey),
                  SizedBox(width: 4),
                  Text(
                    '${protocol['usage_count'] ?? 0} uses',
                    style: TextStyle(color: Colors.grey[600], fontSize: 12),
                  ),
                  Spacer(),
                  Text(
                    _formatDate(protocol['updated_at']),
                    style: TextStyle(color: Colors.grey[600], fontSize: 12),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _formatDate(dynamic dateStr) {
    if (dateStr == null) return '';
    try {
      final date = DateTime.parse(dateStr);
      return '${date.day}/${date.month}/${date.year}';
    } catch (e) {
      return '';
    }
  }
}
