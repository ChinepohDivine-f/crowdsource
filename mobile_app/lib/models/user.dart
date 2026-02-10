class User {
  final String id;
  final String email;
  final String role;
  final bool isActive;

  User({
    required this.id,
    required this.email,
    required this.role,
    required this.isActive,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'],
      email: json['email'],
      role: json['role'],
      isActive: json['is_active'] ?? true, // API might return is_active
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'email': email,
      'role': role,
      'is_active': isActive,
    };
  }

  bool get isAdmin => role == 'ADMIN';
}
