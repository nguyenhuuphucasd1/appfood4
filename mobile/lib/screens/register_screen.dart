import 'package:flutter/material.dart';

import '../theme/app_theme.dart';
import '../state/app_state.dart';
import '../services/api_client.dart';
import '../widgets/app_logo.dart';
import 'main_shell.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  bool _obscure = true;
  bool _loading = false;
  final _formKey = GlobalKey<FormState>();
  final _name = TextEditingController();
  final _email = TextEditingController();
  final _password = TextEditingController();
  final _confirmation = TextEditingController();

  @override
  void dispose() {
    _name.dispose();
    _email.dispose();
    _password.dispose();
    _confirmation.dispose();
    super.dispose();
  }

  Future<void> _register() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    setState(() => _loading = true);
    try {
      await AppStateScope.of(context)
          .register(_name.text, _email.text, _password.text);
      if (!mounted) return;
      Navigator.of(context).pushAndRemoveUntil(
        MaterialPageRoute(builder: (_) => const MainShell()),
        (_) => false,
      );
    } on ApiException catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(error.message)));
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _backToLogin() => Navigator.of(context).pop();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 520),
            child: Stack(
              children: [
                Positioned(
                  top: 0,
                  left: 0,
                  right: 0,
                  height: 330,
                  child: Image.asset(
                    'assets/images/auth_illustration.png',
                    fit: BoxFit.cover,
                    alignment: Alignment.topCenter,
                  ),
                ),
                SingleChildScrollView(
                  padding: const EdgeInsets.only(top: 285),
                  child: Container(
                    width: double.infinity,
                    padding: const EdgeInsets.fromLTRB(22, 26, 22, 30),
                    decoration: const BoxDecoration(
                      color: AppColors.cream,
                      borderRadius: BorderRadius.vertical(
                        top: Radius.circular(32),
                      ),
                    ),
                    child: Form(
                      key: _formKey,
                      child: Column(
                        children: [
                          const AppLogo(compact: true),
                          const SizedBox(height: 18),
                          Text(
                            'Đăng ký',
                            style: Theme.of(context).textTheme.headlineMedium,
                          ),
                          const SizedBox(height: 5),
                          Text(
                            'Tạo tài khoản để khám phá ẩm thực Việt Nam',
                            textAlign: TextAlign.center,
                            style: Theme.of(context).textTheme.bodyMedium,
                          ),
                          const SizedBox(height: 22),
                          TextFormField(
                            controller: _name,
                            validator: (value) =>
                                (value?.trim().length ?? 0) >= 2
                                ? null
                                : 'Hãy nhập họ và tên',
                            decoration: InputDecoration(
                              prefixIcon: Icon(Icons.person_outline_rounded),
                              hintText: 'Họ và tên',
                            ),
                          ),
                          const SizedBox(height: 12),
                          TextFormField(
                            controller: _email,
                            keyboardType: TextInputType.emailAddress,
                            validator: (value) =>
                                value != null && value.contains('@')
                                ? null
                                : 'Hãy nhập email hợp lệ',
                            decoration: InputDecoration(
                              prefixIcon: Icon(Icons.mail_outline_rounded),
                              hintText: 'Email',
                            ),
                          ),
                          const SizedBox(height: 12),
                          TextField(
                            controller: _password,
                            obscureText: _obscure,
                            decoration: InputDecoration(
                              prefixIcon: const Icon(
                                Icons.lock_outline_rounded,
                              ),
                              hintText: 'Mật khẩu',
                              suffixIcon: IconButton(
                                onPressed: () =>
                                    setState(() => _obscure = !_obscure),
                                icon: const Icon(Icons.visibility_off_outlined),
                              ),
                            ),
                          ),
                          const SizedBox(height: 12),
                          TextFormField(
                            controller: _confirmation,
                            obscureText: true,
                            validator: (value) {
                              if (_password.text.length < 8) {
                                return 'Mật khẩu cần ít nhất 8 ký tự';
                              }
                              return value == _password.text
                                  ? null
                                  : 'Mật khẩu xác nhận chưa khớp';
                            },
                            decoration: InputDecoration(
                              prefixIcon: Icon(Icons.lock_reset_rounded),
                              hintText: 'Xác nhận mật khẩu',
                            ),
                          ),
                          const SizedBox(height: 20),
                          ElevatedButton(
                            style: ElevatedButton.styleFrom(
                              backgroundColor: AppColors.orange,
                            ),
                            onPressed: _loading ? null : _register,
                            child: Text(
                              _loading ? 'Đang tạo tài khoản...' : 'Đăng ký',
                            ),
                          ),
                          const SizedBox(height: 16),
                          TextButton(
                            onPressed: _backToLogin,
                            child: const Text('Đã có tài khoản?  Đăng nhập'),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
                Positioned(
                  top: 12,
                  left: 14,
                  child: CircleAvatar(
                    backgroundColor: Colors.white,
                    child: BackButton(
                      key: const Key('register-back-button'),
                      onPressed: _backToLogin,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
