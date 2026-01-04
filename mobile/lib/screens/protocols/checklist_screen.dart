/// Checklist Screen
///
/// Interactive procedural checklist with completion tracking.

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class ChecklistScreen extends StatefulWidget {
  @override
  _ChecklistScreenState createState() => _ChecklistScreenState();
}

class _ChecklistScreenState extends State<ChecklistScreen> {
  List<dynamic> checklists = [];
  Map<String, dynamic>? selectedChecklist;
  Map<String, dynamic>? execution;
  Map<String, bool> itemStatuses = {};
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    fetchChecklists();
  }

  Future<void> fetchChecklists() async {
    setState(() => isLoading = true);

    try {
      final response = await http.get(
        Uri.parse('https://api.dora.app/api/v1/protocols/checklists/'),
        headers: {
          'Authorization': 'Bearer ${await getAccessToken()}',
        },
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        setState(() {
          checklists = [
            ...(data['default_checklists'] ?? []),
            ...(data['checklists'] ?? []),
          ];
          isLoading = false;
        });
      }
    } catch (e) {
      setState(() => isLoading = false);
    }
  }

  Future<String> getAccessToken() async {
    return 'your_access_token';
  }

  Future<void> startChecklist(String checklistId) async {
    try {
      final response = await http.post(
        Uri.parse('https://api.dora.app/api/v1/protocols/checklists/$checklistId/start'),
        headers: {
          'Authorization': 'Bearer ${await getAccessToken()}',
        },
      );

      if (response.statusCode == 200) {
        setState(() {
          execution = json.decode(response.body);
          itemStatuses.clear();
        });
      }
    } catch (e) {
      print('Error starting checklist: $e');
    }
  }

  void toggleItem(String itemId) {
    setState(() {
      itemStatuses[itemId] = !(itemStatuses[itemId] ?? false);
    });
  }

  double getCompletionPercentage() {
    if (selectedChecklist == null) return 0;
    final items = List<Map<String, dynamic>>.from(selectedChecklist!['items'] ?? []);
    if (items.isEmpty) return 0;

    final completed = items.where((item) => itemStatuses[item['id']] == true).length;
    return (completed / items.length) * 100;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Procedural Checklists'),
      ),
      body: isLoading
          ? Center(child: CircularProgressIndicator())
          : selectedChecklist == null
              ? _buildChecklistList()
              : _buildChecklistDetail(),
    );
  }

  Widget _buildChecklistList() {
    return ListView.builder(
      padding: EdgeInsets.all(16),
      itemCount: checklists.length,
      itemBuilder: (context, index) {
        final checklist = checklists[index];
        return Card(
          margin: EdgeInsets.only(bottom: 12),
          child: ListTile(
            title: Text(
              checklist['title'] ?? '',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            subtitle: Text(
              '${(checklist['items'] as List).length} items',
              style: TextStyle(color: Colors.grey),
            ),
            trailing: Icon(Icons.chevron_right),
            onTap: () {
              setState(() {
                selectedChecklist = checklist;
                execution = null;
                itemStatuses.clear();
              });
            },
          ),
        );
      },
    );
  }

  Widget _buildChecklistDetail() {
    final items = List<Map<String, dynamic>>.from(selectedChecklist!['items'] ?? []);

    // Group by section
    final Map<String, List<Map<String, dynamic>>> sections = {};
    for (var item in items) {
      final section = item['section'] ?? 'General';
      if (!sections.containsKey(section)) {
        sections[section] = [];
      }
      sections[section]!.add(item);
    }

    return Column(
      children: [
        // Header
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
                      selectedChecklist!['title'] ?? '',
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  IconButton(
                    icon: Icon(Icons.close),
                    onPressed: () {
                      setState(() {
                        selectedChecklist = null;
                        execution = null;
                      });
                    },
                  ),
                ],
              ),
              Text(
                selectedChecklist!['description'] ?? '',
                style: TextStyle(color: Colors.grey[700]),
              ),
              SizedBox(height: 12),
              if (execution == null)
                ElevatedButton.icon(
                  onPressed: () => startChecklist(selectedChecklist!['id']),
                  icon: Icon(Icons.play_arrow),
                  label: Text('Start Checklist'),
                ),
            ],
          ),
        ),

        // Checklist Items
        Expanded(
          child: ListView(
            padding: EdgeInsets.all(16),
            children: sections.entries.map((entry) {
              return Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Section Header
                  Padding(
                    padding: EdgeInsets.symmetric(vertical: 12),
                    child: Text(
                      entry.key,
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        color: Colors.blue[700],
                      ),
                    ),
                  ),

                  // Section Items
                  ...entry.value.map((item) => _buildChecklistItem(item)),

                  SizedBox(height: 8),
                ],
              );
            }).toList(),
          ),
        ),

        // Progress Bar
        if (execution != null)
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
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      'Completion',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Text(
                      '${getCompletionPercentage().round()}%',
                      style: TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                        color: Colors.blue,
                      ),
                    ),
                  ],
                ),
                SizedBox(height: 8),
                LinearProgressIndicator(
                  value: getCompletionPercentage() / 100,
                  backgroundColor: Colors.grey[200],
                  minHeight: 8,
                ),
                SizedBox(height: 12),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: getCompletionPercentage() == 100
                        ? () {
                            showDialog(
                              context: context,
                              builder: (context) => AlertDialog(
                                title: Text('Complete Checklist'),
                                content: Text('Mark this checklist as completed?'),
                                actions: [
                                  TextButton(
                                    onPressed: () => Navigator.pop(context),
                                    child: Text('Cancel'),
                                  ),
                                  ElevatedButton(
                                    onPressed: () {
                                      Navigator.pop(context);
                                      setState(() {
                                        selectedChecklist = null;
                                        execution = null;
                                      });
                                    },
                                    child: Text('Complete'),
                                  ),
                                ],
                              ),
                            );
                          }
                        : null,
                    child: Text('Complete Checklist'),
                  ),
                ),
              ],
            ),
          ),
      ],
    );
  }

  Widget _buildChecklistItem(Map<String, dynamic> item) {
    final itemId = item['id'];
    final isCompleted = itemStatuses[itemId] ?? false;

    return Card(
      margin: EdgeInsets.only(bottom: 8),
      child: CheckboxListTile(
        title: Text(
          item['text'] ?? '',
          style: TextStyle(
            decoration: isCompleted ? TextDecoration.lineThrough : null,
            color: isCompleted ? Colors.grey : Colors.black,
          ),
        ),
        subtitle: item['notes'] != null
            ? Text(item['notes'], style: TextStyle(fontSize: 12))
            : null,
        value: isCompleted,
        onChanged: execution != null
            ? (value) => toggleItem(itemId)
            : null,
        secondary: item['required'] == true
            ? Icon(Icons.star, color: Colors.red, size: 16)
            : null,
        controlAffinity: ListTileControlAffinity.leading,
      ),
    );
  }
}
