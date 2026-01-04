import 'package:flutter/material.dart';

/// Specialist Directory Screen
///
/// Browse and search verified specialists by specialty, location, ratings.
class SpecialistDirectoryScreen extends StatefulWidget {
  const SpecialistDirectoryScreen({Key? key}) : super(key: key);

  @override
  State<SpecialistDirectoryScreen> createState() =>
      _SpecialistDirectoryScreenState();
}

class _SpecialistDirectoryScreenState extends State<SpecialistDirectoryScreen> {
  String selectedSpecialty = 'all';
  String searchCity = '';

  // Mock data
  final specialists = [
    {
      'id': '1',
      'name': 'Dr. Rajesh Kumar',
      'specialty': 'Cardiology',
      'city': 'Mumbai',
      'rating': 4.8,
      'consultations': 156,
      'verificationLevel': 'expert',
      'fee': 500,
      'responseTime': '12 hours',
    },
    {
      'id': '2',
      'name': 'Dr. Priya Sharma',
      'specialty': 'Neurology',
      'city': 'Delhi',
      'rating': 4.9,
      'consultations': 203,
      'verificationLevel': 'certified',
      'fee': 600,
      'responseTime': '8 hours',
    },
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Find Specialists'),
        backgroundColor: Colors.blue,
      ),
      body: Column(
        children: [
          // Filters
          Container(
            padding: const EdgeInsets.all(16),
            color: Colors.grey.shade100,
            child: Column(
              children: [
                DropdownButtonFormField<String>(
                  value: selectedSpecialty,
                  decoration: const InputDecoration(
                    labelText: 'Specialty',
                    filled: true,
                    fillColor: Colors.white,
                    border: OutlineInputBorder(),
                  ),
                  items: [
                    'all',
                    'cardiology',
                    'neurology',
                    'pulmonology',
                    'gastroenterology'
                  ]
                      .map((s) => DropdownMenuItem(
                            value: s,
                            child: Text(s == 'all'
                                ? 'All Specialties'
                                : s[0].toUpperCase() + s.substring(1)),
                          ))
                      .toList(),
                  onChanged: (value) {
                    setState(() {
                      selectedSpecialty = value!;
                    });
                  },
                ),
                const SizedBox(height: 12),
                TextField(
                  decoration: const InputDecoration(
                    labelText: 'City',
                    hintText: 'Search by city',
                    filled: true,
                    fillColor: Colors.white,
                    border: OutlineInputBorder(),
                    prefixIcon: Icon(Icons.search),
                  ),
                  onChanged: (value) {
                    setState(() {
                      searchCity = value;
                    });
                  },
                ),
              ],
            ),
          ),

          // Specialists List
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: specialists.length,
              itemBuilder: (context, index) {
                final specialist = specialists[index];
                return Card(
                  margin: const EdgeInsets.only(bottom: 16),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Expanded(
                              child: Text(
                                specialist['name'] as String,
                                style: const TextStyle(
                                  fontSize: 18,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                            if (specialist['verificationLevel'] == 'expert')
                              Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 8,
                                  vertical: 4,
                                ),
                                decoration: BoxDecoration(
                                  color: Colors.yellow.shade100,
                                  borderRadius: BorderRadius.circular(4),
                                ),
                                child: const Text(
                                  '⭐⭐⭐ Expert',
                                  style: TextStyle(fontSize: 12),
                                ),
                              ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Text(
                          '${specialist['specialty']} • ${specialist['city']}',
                          style: const TextStyle(color: Colors.grey),
                        ),
                        const SizedBox(height: 16),
                        Row(
                          children: [
                            _buildStat(
                              '${specialist['rating']} ⭐',
                              'Rating',
                            ),
                            _buildStat(
                              '${specialist['consultations']}',
                              'Consultations',
                            ),
                            _buildStat(
                              '₹${specialist['fee']}',
                              'Fee',
                            ),
                          ],
                        ),
                        const SizedBox(height: 16),
                        SizedBox(
                          width: double.infinity,
                          child: ElevatedButton(
                            onPressed: () {
                              // Navigate to consultation request
                            },
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.blue,
                            ),
                            child: const Text('Request Consultation'),
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStat(String value, String label) {
    return Expanded(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: const TextStyle(
              fontSize: 12,
              color: Colors.grey,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            value,
            style: const TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }
}
