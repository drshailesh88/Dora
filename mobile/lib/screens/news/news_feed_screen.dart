import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class NewsArticle {
  final String id;
  final String title;
  final String? subtitle;
  final String url;
  final String source;
  final String category;
  final DateTime publicationDate;
  final String summary;
  final List<String> keyFindings;
  final String? clinicalImplications;
  final List<String> specialty;
  final String priority;
  final int readingTimeMinutes;

  NewsArticle({
    required this.id,
    required this.title,
    this.subtitle,
    required this.url,
    required this.source,
    required this.category,
    required this.publicationDate,
    required this.summary,
    required this.keyFindings,
    this.clinicalImplications,
    required this.specialty,
    required this.priority,
    required this.readingTimeMinutes,
  });

  factory NewsArticle.fromJson(Map<String, dynamic> json) {
    return NewsArticle(
      id: json['id'],
      title: json['title'],
      subtitle: json['subtitle'],
      url: json['url'],
      source: json['source'],
      category: json['category'],
      publicationDate: DateTime.parse(json['publication_date']),
      summary: json['summary'],
      keyFindings: List<String>.from(json['key_findings'] ?? []),
      clinicalImplications: json['clinical_implications'],
      specialty: List<String>.from(json['specialty'] ?? []),
      priority: json['priority'],
      readingTimeMinutes: json['reading_time_minutes'],
    );
  }
}

class NewsFeedScreen extends StatefulWidget {
  const NewsFeedScreen({Key? key}) : super(key: key);

  @override
  State<NewsFeedScreen> createState() => _NewsFeedScreenState();
}

class _NewsFeedScreenState extends State<NewsFeedScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  List<NewsArticle> _articles = [];
  bool _loading = true;
  String _selectedCategory = 'all';

  final List<String> _categories = [
    'all',
    'research',
    'guidelines',
    'drug_approvals',
    'conferences',
    'clinical_practice',
  ];

  final Map<String, String> _categoryNames = {
    'all': 'All',
    'research': 'Research',
    'guidelines': 'Guidelines',
    'drug_approvals': 'Drug Approvals',
    'conferences': 'Conferences',
    'clinical_practice': 'Clinical Practice',
  };

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _tabController.addListener(_handleTabChange);
    _fetchArticles();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  void _handleTabChange() {
    if (_tabController.indexIsChanging) {
      _fetchArticles();
    }
  }

  Future<void> _fetchArticles() async {
    setState(() {
      _loading = true;
    });

    try {
      String endpoint = '/api/v1/news/feed';
      if (_tabController.index == 1) {
        endpoint = '/api/v1/news/trending';
      } else if (_tabController.index == 2) {
        endpoint = '/api/v1/news/breaking';
      }

      final queryParams = _selectedCategory != 'all'
          ? '?category=$_selectedCategory'
          : '';

      // In production, get token from secure storage
      final token = ''; // Get from storage

      final response = await http.get(
        Uri.parse('$endpoint$queryParams'),
        headers: {
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data['success']) {
          setState(() {
            _articles = (data['articles'] as List)
                .map((a) => NewsArticle.fromJson(a))
                .toList();
            _loading = false;
          });
        }
      }
    } catch (e) {
      print('Error fetching articles: $e');
      setState(() {
        _loading = false;
      });
    }
  }

  Color _getPriorityColor(String priority) {
    switch (priority) {
      case 'critical':
        return Colors.red;
      case 'high':
        return Colors.orange;
      case 'medium':
        return Colors.blue;
      default:
        return Colors.grey;
    }
  }

  IconData _getCategoryIcon(String category) {
    switch (category) {
      case 'research':
        return Icons.science;
      case 'guidelines':
        return Icons.assignment;
      case 'drug_approvals':
        return Icons.medication;
      case 'conferences':
        return Icons.school;
      case 'clinical_practice':
        return Icons.medical_services;
      default:
        return Icons.article;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Medical News'),
        backgroundColor: Colors.indigo,
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: 'Feed'),
            Tab(text: '🔥 Trending'),
            Tab(text: '⚡ Breaking'),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.search),
            onPressed: () {
              // Navigate to search
            },
          ),
          IconButton(
            icon: const Icon(Icons.bookmarks),
            onPressed: () {
              // Navigate to bookmarks
            },
          ),
        ],
      ),
      body: Column(
        children: [
          // Category Filter
          Container(
            height: 50,
            color: Colors.white,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              itemCount: _categories.length,
              itemBuilder: (context, index) {
                final category = _categories[index];
                final isSelected = category == _selectedCategory;

                return Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: FilterChip(
                    label: Text(_categoryNames[category] ?? category),
                    selected: isSelected,
                    onSelected: (selected) {
                      setState(() {
                        _selectedCategory = category;
                      });
                      _fetchArticles();
                    },
                    selectedColor: Colors.indigo.shade100,
                    labelStyle: TextStyle(
                      color: isSelected ? Colors.indigo : Colors.grey.shade700,
                      fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                    ),
                  ),
                );
              },
            ),
          ),

          // Articles List
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : _articles.isEmpty
                    ? const Center(
                        child: Text(
                          'No articles found',
                          style: TextStyle(color: Colors.grey),
                        ),
                      )
                    : RefreshIndicator(
                        onRefresh: _fetchArticles,
                        child: ListView.builder(
                          itemCount: _articles.length,
                          itemBuilder: (context, index) {
                            return _buildArticleCard(_articles[index]);
                          },
                        ),
                      ),
          ),
        ],
      ),
    );
  }

  Widget _buildArticleCard(NewsArticle article) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      elevation: 2,
      child: InkWell(
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => ArticleDetailScreen(article: article),
            ),
          );
        },
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Priority Badge
              if (article.priority != 'low')
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: _getPriorityColor(article.priority).withOpacity(0.1),
                    border: Border.all(
                      color: _getPriorityColor(article.priority),
                      width: 1,
                    ),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    article.priority.toUpperCase(),
                    style: TextStyle(
                      color: _getPriorityColor(article.priority),
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),

              const SizedBox(height: 8),

              // Title
              Text(
                article.title,
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),

              const SizedBox(height: 8),

              // Metadata
              Row(
                children: [
                  Icon(
                    _getCategoryIcon(article.category),
                    size: 16,
                    color: Colors.grey,
                  ),
                  const SizedBox(width: 4),
                  Text(
                    article.category.replaceAll('_', ' ').toUpperCase(),
                    style: const TextStyle(
                      fontSize: 12,
                      color: Colors.grey,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    article.source.toUpperCase(),
                    style: const TextStyle(
                      fontSize: 12,
                      color: Colors.grey,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    '${article.readingTimeMinutes} min',
                    style: const TextStyle(
                      fontSize: 12,
                      color: Colors.grey,
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 12),

              // Summary
              Text(
                article.summary,
                maxLines: 3,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  fontSize: 14,
                  color: Colors.black87,
                ),
              ),

              // Key Findings
              if (article.keyFindings.isNotEmpty) ...[
                const SizedBox(height: 12),
                const Text(
                  'Key Findings:',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 4),
                ...article.keyFindings.take(2).map((finding) => Padding(
                      padding: const EdgeInsets.only(left: 8, top: 2),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('• ', style: TextStyle(fontSize: 12)),
                          Expanded(
                            child: Text(
                              finding,
                              style: const TextStyle(fontSize: 12),
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                        ],
                      ),
                    )),
              ],

              // Specialties
              if (article.specialty.isNotEmpty) ...[
                const SizedBox(height: 12),
                Wrap(
                  spacing: 8,
                  runSpacing: 4,
                  children: article.specialty.map((spec) => Chip(
                    label: Text(
                      spec,
                      style: const TextStyle(fontSize: 10),
                    ),
                    backgroundColor: Colors.grey.shade100,
                    padding: const EdgeInsets.symmetric(horizontal: 4),
                    materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                  )).toList(),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

// Placeholder for ArticleDetailScreen
class ArticleDetailScreen extends StatelessWidget {
  final NewsArticle article;

  const ArticleDetailScreen({Key? key, required this.article}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Article Details'),
        backgroundColor: Colors.indigo,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              article.title,
              style: const TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),
            Text(
              article.summary,
              style: const TextStyle(fontSize: 16),
            ),
            // Add more article details here
          ],
        ),
      ),
    );
  }
}
