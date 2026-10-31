import 'package:flutter/material.dart';

import '../services/api_client.dart';
import '../state/app_state.dart';
import '../theme/app_theme.dart';
import 'history_screen.dart';
import 'login_screen.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final state = AppStateScope.of(context);
    final user = state.user;
    return SafeArea(
      child: ListView(
        padding: const EdgeInsets.all(22),
        children: [
          Text('Cá nhân', style: Theme.of(context).textTheme.headlineMedium),
          const SizedBox(height: 22),
          const CircleAvatar(
            radius: 48,
            backgroundColor: AppColors.creamStrong,
            child: Icon(
              Icons.person_rounded,
              size: 48,
              color: AppColors.forest,
            ),
          ),
          const SizedBox(height: 12),
          Center(
            child: Text(
              user?.fullName ?? 'Khách',
              style: Theme.of(context).textTheme.titleLarge,
            ),
          ),
          if (user != null) ...[
            const SizedBox(height: 4),
            Center(
              child: Text(
                user.email,
                style: Theme.of(context).textTheme.bodyMedium,
              ),
            ),
          ],
          const SizedBox(height: 28),
          if (user != null) ...[
            _ActionSetting(
              icon: Icons.edit_outlined,
              title: 'Chỉnh sửa tên',
              subtitle: 'Cập nhật hồ sơ tài khoản',
              onTap: () => _editName(context, state, user.fullName),
            ),
            _ActionSetting(
              icon: Icons.history_rounded,
              title: 'Lịch sử nhận diện',
              subtitle: 'Không lưu ảnh gốc',
              onTap: () => Navigator.of(
                context,
              ).push(MaterialPageRoute(builder: (_) => const HistoryScreen())),
            ),
          ],
          _Setting(
            icon: Icons.cloud_outlined,
            title: 'Backend AI',
            subtitle: ApiConfig.baseUrl,
          ),
          const _Setting(
            icon: Icons.language_rounded,
            title: 'Ngôn ngữ',
            subtitle: 'Tiếng Việt',
          ),
          const _Setting(
            icon: Icons.info_outline_rounded,
            title: 'Phiên bản',
            subtitle: '1.1.0 MVP',
          ),
          const SizedBox(height: 24),
          if (user == null)
            ElevatedButton.icon(
              onPressed: () => Navigator.of(context)
                  .push(MaterialPageRoute(builder: (_) => const LoginScreen())),
              icon: const Icon(Icons.login_rounded),
              label: const Text('Đăng nhập để đồng bộ'),
            )
          else
            OutlinedButton.icon(
              onPressed: () => _logout(context, state),
              icon: const Icon(Icons.logout_rounded),
              label: const Text('Đăng xuất'),
              style: OutlinedButton.styleFrom(
                foregroundColor: AppColors.orange,
                minimumSize: const Size.fromHeight(52),
              ),
            ),
        ],
      ),
    );
  }

  Future<void> _logout(BuildContext context, AppState state) async {
    await state.logout();
    if (!context.mounted) return;
    Navigator.of(context).pushAndRemoveUntil(
      MaterialPageRoute(builder: (_) => const LoginScreen()),
      (_) => false,
    );
  }

  Future<void> _editName(
    BuildContext context,
    AppState state,
    String current,
  ) async {
    await showDialog<bool>(
      context: context,
      builder: (context) => _EditNameDialog(initialName: current, state: state),
    );
  }
}

class _EditNameDialog extends StatefulWidget {
  const _EditNameDialog({required this.initialName, required this.state});

  final String initialName;
  final AppState state;

  @override
  State<_EditNameDialog> createState() => _EditNameDialogState();
}

class _EditNameDialogState extends State<_EditNameDialog> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _controller;
  late final FocusNode _focusNode;
  bool _saving = false;
  String? _serverError;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController(text: widget.initialName);
    _controller.selection = TextSelection.collapsed(
      offset: _controller.text.length,
    );
    _focusNode = FocusNode();
  }

  @override
  void dispose() {
    _focusNode.dispose();
    _controller.dispose();
    super.dispose();
  }

  String? _validateName(String? value) {
    final name = value?.trim() ?? '';
    if (name.isEmpty) return 'Vui lòng nhập họ và tên.';
    if (name.length < 2) return 'Tên phải có ít nhất 2 ký tự.';
    if (name.length > 120) return 'Tên không được vượt quá 120 ký tự.';
    return null;
  }

  Future<void> _submit() async {
    if (_saving || !(_formKey.currentState?.validate() ?? false)) return;
    setState(() {
      _saving = true;
      _serverError = null;
    });
    try {
      await widget.state.updateProfile(_controller.text.trim());
      if (!mounted) return;
      Navigator.of(context).pop(true);
    } on ApiException catch (error) {
      if (!mounted) return;
      setState(() {
        _saving = false;
        _serverError = error.message;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _saving = false;
        _serverError = 'Không thể cập nhật tên. Vui lòng thử lại.';
      });
    }
  }

  @override
  Widget build(BuildContext context) => PopScope(
    canPop: !_saving,
    child: AlertDialog(
      title: const Text('Chỉnh sửa tên'),
      content: Form(
        key: _formKey,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            TextFormField(
              key: const Key('edit-name-field'),
              controller: _controller,
              focusNode: _focusNode,
              autofocus: true,
              enabled: !_saving,
              maxLength: 120,
              textCapitalization: TextCapitalization.words,
              textInputAction: TextInputAction.done,
              autofillHints: const [AutofillHints.name],
              validator: _validateName,
              onChanged: (_) {
                if (_serverError != null) {
                  setState(() => _serverError = null);
                }
              },
              onFieldSubmitted: (_) => _submit(),
              decoration: const InputDecoration(
                labelText: 'Họ và tên',
                counterText: '',
              ),
            ),
            if (_serverError != null) ...[
              const SizedBox(height: 10),
              Text(
                _serverError!,
                key: const Key('edit-name-server-error'),
                style: TextStyle(
                  color: Theme.of(context).colorScheme.error,
                  fontSize: 13,
                ),
              ),
            ],
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: _saving ? null : () => Navigator.pop(context, false),
          child: const Text('Hủy'),
        ),
        FilledButton(
          key: const Key('edit-name-save'),
          onPressed: _saving ? null : _submit,
          child: _saving
              ? const SizedBox.square(
                  dimension: 18,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Text('Lưu'),
        ),
      ],
    ),
  );
}

class _Setting extends StatelessWidget {
  const _Setting({
    required this.icon,
    required this.title,
    required this.subtitle,
  });
  final IconData icon;
  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) => ListTile(
    contentPadding: const EdgeInsets.symmetric(vertical: 5),
    leading: CircleAvatar(
      backgroundColor: AppColors.forest.withValues(alpha: .1),
      child: Icon(icon, color: AppColors.forest),
    ),
    title: Text(title, style: const TextStyle(fontWeight: FontWeight.w700)),
    subtitle: Text(subtitle),
  );
}

class _ActionSetting extends StatelessWidget {
  const _ActionSetting({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.onTap,
  });
  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => ListTile(
    onTap: onTap,
    contentPadding: const EdgeInsets.symmetric(vertical: 5),
    leading: CircleAvatar(
      backgroundColor: AppColors.forest.withValues(alpha: .1),
      child: Icon(icon, color: AppColors.forest),
    ),
    title: Text(title, style: const TextStyle(fontWeight: FontWeight.w700)),
    subtitle: Text(subtitle),
    trailing: const Icon(Icons.chevron_right_rounded),
  );
}
