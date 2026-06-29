require 'securerandom'

module HomeAssistantIngressAuth
  SECRET_HEADER = 'HTTP_X_DAWARICH_INGRESS_SECRET'
  USER_ID_HEADER = 'HTTP_X_REMOTE_USER_ID'
  USER_NAME_HEADER = 'HTTP_X_REMOTE_USER_NAME'
  DISPLAY_NAME_HEADER = 'HTTP_X_REMOTE_USER_DISPLAY_NAME'

  module_function

  def enabled?
    ENV['INGRESS_AUTH_SECRET'].to_s != ''
  end

  def authenticated_request?(request)
    enabled? && request.get_header(SECRET_HEADER) == ENV['INGRESS_AUTH_SECRET'].to_s && request.get_header(USER_ID_HEADER).to_s != ''
  end

  def user_for(request)
    ha_user_id = request.get_header(USER_ID_HEADER).to_s.strip
    email = "ha-#{ha_user_id}@homeassistant.local"
    user = User.find_or_initialize_by(email: email)

    if user.new_record?
      password = SecureRandom.hex(32)
      user.password = password
      user.password_confirmation = password
    end

    display_name = request.get_header(DISPLAY_NAME_HEADER).to_s.strip
    user_name = request.get_header(USER_NAME_HEADER).to_s.strip
    preferred_name = display_name != '' ? display_name : user_name

    if preferred_name != ''
      user.name = preferred_name if user.respond_to?(:name=)
      user.username = preferred_name if user.respond_to?(:username=)
    end

    user.save! if user.new_record? || user.changed?
    user
  end
end

ActiveSupport.on_load(:action_controller_base) do
  prepend_before_action :home_assistant_ingress_sign_in

  private

  def home_assistant_ingress_sign_in
    return unless HomeAssistantIngressAuth.authenticated_request?(request)

    user = HomeAssistantIngressAuth.user_for(request)
    request.env['warden'].set_user(user, scope: :user)

    return unless request.path.match?(%r{/(users|admin|account)/sign_in\z|/users/sign_up\z|/users/password/new\z})

    redirect_to(root_path)
  rescue StandardError => e
    Rails.logger.warn("Home Assistant ingress auth failed: #{e.class}: #{e.message}")
  end
end