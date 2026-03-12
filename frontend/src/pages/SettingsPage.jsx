import { useState } from 'react'
import { Settings, User, Lock, Loader2, CheckCircle, ChevronDown } from 'lucide-react'
import toast from 'react-hot-toast'
import useAuthStore from '../store/authStore'
import { authAPI } from '../services/api'
import { ROLES, EXPERIENCE_LEVELS } from '../data/options'

const groupedRoles = ROLES.reduce((acc, r) => {
  if (!acc[r.group]) acc[r.group] = []
  acc[r.group].push(r)
  return acc
}, {})

function Section({ title, icon: Icon, children }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
      <div className="flex items-center gap-2 mb-5">
        <Icon size={16} className="text-indigo-400" />
        <h2 className="text-sm font-semibold text-white uppercase tracking-wider">{title}</h2>
      </div>
      {children}
    </div>
  )
}

export default function SettingsPage() {
  const { user, setUser } = useAuthStore()

  const [profile, setProfile] = useState({
    full_name: user?.full_name || '',
    target_role: user?.target_role || 'software_engineer',
    experience_level: user?.experience_level || 'junior',
  })
  const [passwords, setPasswords] = useState({ current_password: '', new_password: '', confirm: '' })
  const [savingProfile, setSavingProfile] = useState(false)
  const [savingPassword, setSavingPassword] = useState(false)
  const [profileSaved, setProfileSaved] = useState(false)

  const currentRoleLabel = ROLES.find(r => r.value === profile.target_role)?.label || profile.target_role

  const saveProfile = async () => {
    setSavingProfile(true)
    try {
      const { data } = await authAPI.updateMe({
        full_name: profile.full_name,
        target_role: profile.target_role,
        experience_level: profile.experience_level,
      })
      setUser(data)
      setProfileSaved(true)
      toast.success('Profile updated!')
      setTimeout(() => setProfileSaved(false), 2500)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to update profile')
    } finally {
      setSavingProfile(false)
    }
  }

  const savePassword = async () => {
    if (passwords.new_password !== passwords.confirm) {
      toast.error('Passwords do not match')
      return
    }
    if (passwords.new_password.length < 8) {
      toast.error('Password must be at least 8 characters')
      return
    }
    setSavingPassword(true)
    try {
      await authAPI.changePassword({
        current_password: passwords.current_password,
        new_password: passwords.new_password,
      })
      toast.success('Password changed!')
      setPasswords({ current_password: '', new_password: '', confirm: '' })
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to change password')
    } finally {
      setSavingPassword(false)
    }
  }

  return (
    <div className="p-8 max-w-2xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="text-gray-400 mt-1">Manage your profile and preferences</p>
      </div>

      <div className="space-y-5">
        {/* Profile */}
        <Section title="Profile" icon={User}>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Full Name</label>
              <input value={profile.full_name} onChange={e => setProfile({ ...profile, full_name: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500 transition-colors" />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Email</label>
              <input value={user?.email} disabled
                className="w-full bg-gray-800/50 border border-gray-700 rounded-lg px-4 py-2.5 text-gray-500 cursor-not-allowed" />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Target Role</label>
              <select value={profile.target_role} onChange={e => setProfile({ ...profile, target_role: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500 transition-colors">
                {Object.entries(groupedRoles).map(([group, roles]) => (
                  <optgroup key={group} label={group}>
                    {roles.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
                  </optgroup>
                ))}
              </select>
              <p className="text-xs text-gray-500 mt-1.5">
                Currently preparing for: <span className="text-indigo-400 font-medium">{currentRoleLabel}</span>
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Experience Level</label>
              <div className="grid grid-cols-3 gap-2">
                {EXPERIENCE_LEVELS.map(l => (
                  <button key={l.value} onClick={() => setProfile({ ...profile, experience_level: l.value })}
                    className={`py-2 px-3 rounded-lg text-xs font-medium transition-all ${
                      profile.experience_level === l.value
                        ? 'bg-indigo-600 text-white'
                        : 'bg-gray-800 text-gray-400 hover:text-white hover:bg-gray-700'
                    }`}>
                    {l.label}
                  </button>
                ))}
              </div>
            </div>

            <button onClick={saveProfile} disabled={savingProfile}
              className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-xl text-sm font-medium transition-colors">
              {savingProfile
                ? <Loader2 size={15} className="animate-spin" />
                : profileSaved
                  ? <CheckCircle size={15} />
                  : <Settings size={15} />
              }
              {savingProfile ? 'Saving...' : profileSaved ? 'Saved!' : 'Save Profile'}
            </button>
          </div>
        </Section>

        {/* Password */}
        <Section title="Change Password" icon={Lock}>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Current Password</label>
              <input type="password" value={passwords.current_password}
                onChange={e => setPasswords({ ...passwords, current_password: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500 transition-colors"
                placeholder="Enter current password" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">New Password</label>
              <input type="password" value={passwords.new_password}
                onChange={e => setPasswords({ ...passwords, new_password: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500 transition-colors"
                placeholder="Min 8 characters" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Confirm New Password</label>
              <input type="password" value={passwords.confirm}
                onChange={e => setPasswords({ ...passwords, confirm: e.target.value })}
                className={`w-full bg-gray-800 border rounded-lg px-4 py-2.5 text-white focus:outline-none transition-colors ${
                  passwords.confirm && passwords.confirm !== passwords.new_password
                    ? 'border-red-500'
                    : 'border-gray-700 focus:border-indigo-500'
                }`}
                placeholder="Repeat new password" />
              {passwords.confirm && passwords.confirm !== passwords.new_password && (
                <p className="text-xs text-red-400 mt-1">Passwords do not match</p>
              )}
            </div>
            <button onClick={savePassword} disabled={savingPassword}
              className="flex items-center gap-2 px-5 py-2.5 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 text-white rounded-xl text-sm font-medium transition-colors">
              {savingPassword ? <Loader2 size={15} className="animate-spin" /> : <Lock size={15} />}
              {savingPassword ? 'Changing...' : 'Change Password'}
            </button>
          </div>
        </Section>

        {/* Account info */}
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
          <p className="text-xs text-gray-500">
            Member since {user?.created_at ? new Date(user.created_at).toLocaleDateString('en-IN', { year: 'numeric', month: 'long', day: 'numeric' }) : '—'}
          </p>
        </div>
      </div>
    </div>
  )
}