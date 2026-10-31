class UserProfile {
  const UserProfile({
    required this.id,
    required this.email,
    required this.fullName,
  });

  final int id;
  final String email;
  final String fullName;

  factory UserProfile.fromJson(Map<String, dynamic> json) => UserProfile(
    id: json['id'] as int? ?? 0,
    email: json['email'] as String? ?? '',
    fullName: json['fullName'] as String? ?? '',
  );
}
